import json
import asyncio
import time
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Literal, Optional
from supabase import create_client, Client, ClientOptions
from core.config.init_storage import init_storage
from core.models.account_profile import AccountProfile
from core.services.account_profile_service import AccountProfileService
import logging
import logging.config
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from core.main_process import run_main_process
from core.services.status_updates import StatusService
from core.content.image_generation.carousel_generator import CarouselGenerator

# Set up basic & console logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
)
logger = logging.getLogger(__name__)

# Load environment from .env if present
load_dotenv()
logger.info("==== [MODULE SCOPE] Starting up main.py ====")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==== [LIFESPAN] Entering lifespan context ====")
    try:
        # Create a client just for init_storage
        supabase_for_init = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        )
        logger.info("[LIFESPAN] calling init_storage()...")
        await init_storage(supabase_for_init)
        logger.info("[LIFESPAN] init_storage() done.")
    except Exception as e:
        logger.error("[LIFESPAN] Error during initialization", exc_info=True)
        # Don't re-raise; allow degraded startup
    yield
    logger.info("==== [LIFESPAN] Exiting lifespan context ====")


# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

# Log minimal environment info
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
logger.info(f"SUPABASE_URL present? {'Yes' if supabase_url else 'No'}")
logger.info(f"SUPABASE_SERVICE_ROLE_KEY present? {'Yes' if supabase_key else 'No'}")

# Ensure required env
if not supabase_url or not supabase_key:
    logger.error("==== Missing required environment variables for Supabase! ====")
    raise ValueError("Missing required Supabase environment variables")

# Create global Supabase client
logger.info("==== Creating global Supabase client... ====")
supabase: Client = create_client(supabase_url, supabase_key)
logger.info("==== Global Supabase client created successfully ====")


def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> tuple[Client, dict]:
    """
    Auth flow requiring a Bearer token.
    Returns (Supabase client for this token, user record).
    """
    logger.info("==== [AUTHENTICATE] CALLED ====")
    try:
        if credentials.scheme != "Bearer":
            raise ValueError("Invalid authorization scheme")

        logger.info("Creating Supabase client in authenticate() with Bearer token...")
        supabase_auth = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            options=ClientOptions(
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            ),
        )
        logger.info("Supabase client created. Checking user...")

        user_response = supabase_auth.auth.get_user(credentials.credentials)
        if not user_response or not user_response.user:
            raise ValueError("User not found")

        logger.info(f"User authenticated successfully: {user_response.user}")
        return supabase_auth, user_response.user

    except Exception:
        logger.error("==== [AUTHENTICATE] CRASH ====", exc_info=True)
        raise HTTPException(status_code=401, detail="Failed to authenticate")


@app.get("/health")
async def health_check():
    """
    Simple endpoint to confirm the server is running
    without any authentication.
    """
    logger.info("==== [HEALTH] CALLED ====")
    return {"status": "ok"}


@app.get("/")
async def root():
    logger.info("==== [ROOT ENDPOINT] CALLED ====")
    return {"message": "PostOnce API is running"}


class ContentGenerationRequest(BaseModel):
    account_id: str
    content_id: str
    post_id: Optional[str] = None
    content: Optional[str] = None
    content_type: Literal[
        "precta_tweet",
        "postcta_tweet",
        "thread_tweet",
        "long_form_tweet",
        "long_form_post",
        "image_list",
        "carousel_tweet",
        "carousel_post",
    ]

    def validate_request(self):
        """
        Confirms that EXACTLY one of `post_id` or `content` is provided.
        """
        logger.info("==== [ContentGenerationRequest] validate_request CALLED ====")
        if bool(self.post_id) == bool(self.content):
            raise ValueError("Exactly one of post_id or content must be provided")


@app.post("/generate_content")
async def generate_content_endpoint(
    request: ContentGenerationRequest,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    logger.info("==== [generate_content_endpoint] CALLED ====")
    try:
        logger.info(f"[generate_content_endpoint] request.body={request.dict()}")
        request.validate_request()
        logger.info("[generate_content_endpoint] Validation success")

        account_profile_service = AccountProfileService(client_user[0])
        logger.info(
            f"[generate_content_endpoint] fetching account profile for {request.account_id}"
        )
        account_profile = await account_profile_service.get_account_profile(
            request.account_id
        )

        if not account_profile:
            logger.error(
                f"[generate_content_endpoint] No account profile found for {request.account_id}"
            )
            raise HTTPException(status_code=404, detail="Account profile not found")

        logger.info(
            f"[generate_content_endpoint] Account profile found: {account_profile}"
        )

        return StreamingResponse(
            content_generator(
                account_profile,
                request.content_id,
                request.post_id,
                request.content_type,
                client_user[0],
                request.content,
            ),
            media_type="text/event-stream",
        )
    except ValueError as ve:
        logger.error("==== [generate_content_endpoint] ValueError ====", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("==== [generate_content_endpoint] CRASH ====", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def content_generator(
    account_profile: AccountProfile,
    content_id: str,
    post_id: Optional[str],
    content_type: str,
    supabase: Client,
    content: Optional[str] = None,
):
    start_time = time.time()
    logger.info(f"==== [content_generator] START for content_id={content_id} ====")
    try:
        status_service = StatusService(supabase)

        logger.info(
            f"==== [content_generator] Yielding 'started' message for {content_id}"
        )
        start_message = {
            "status": "started",
            "message": "Initializing content generation and editing",
        }
        yield json.dumps(start_message) + "\n"

        logger.info(
            f"==== [content_generator] About to call run_main_process() for {content_id} ===="
        )
        result = await run_main_process(
            account_profile,
            content_id,
            post_id,
            content_type,
            supabase,
            content,
        )
        logger.info(
            f"==== [content_generator] run_main_process() returned: {result} ===="
        )

        if not isinstance(result, dict):
            logger.error("==== [content_generator] result is not a dict! ====")
            await status_service.update_status(content_id, "failed")
            error_message = {
                "status": "failed",
                "error": "Invalid result format",
                "total_time": f"{time.time() - start_time:.2f} seconds",
            }
            yield json.dumps(error_message) + "\n"
            return

        if result.get("success", False):
            logger.info(f"==== [content_generator] success for {content_id} ====")
            await status_service.update_status(content_id, "generated")
            success_message = {
                "status": "completed",
                "result": result,
                "total_time": f"{time.time() - start_time:.2f} seconds",
            }
            yield json.dumps(success_message) + "\n"
        else:
            error_msg = result.get("error", "Unknown error during content generation")
            logger.error(f"==== [content_generator] failed with {error_msg}")
            await status_service.update_status(content_id, "failed")
            error_message = {
                "status": "failed",
                "error": error_msg,
                "total_time": f"{time.time() - start_time:.2f} seconds",
            }
            yield json.dumps(error_message) + "\n"

    except Exception as e:
        logger.error(
            f"==== [content_generator] EXCEPTION for {content_id} ====", exc_info=True
        )
        status_service = StatusService(supabase)
        await status_service.update_status(content_id, "failed")
        exception_message = {
            "status": "failed",
            "error": str(e),
            "total_time": f"{time.time() - start_time:.2f} seconds",
        }
        yield json.dumps(exception_message) + "\n"
    finally:
        logger.info(f"==== [content_generator] DONE for {content_id} ====")


# If needed for local debugging:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
