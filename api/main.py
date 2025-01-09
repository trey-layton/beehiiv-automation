import json
import asyncio
import time
import os
import sys
import atexit
import traceback
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
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from core.main_process import run_main_process
from core.services.status_updates import StatusService
from core.content.image_generation.carousel_generator import CarouselGenerator
import pkg_resources

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Set up exception hook to catch uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


# atexit handler to log process exit details
def on_exit():
    logger.info("==== Python process is exiting ====")
    logger.info(f"Python version: {sys.version}")
    # Log installed packages
    try:
        installed_packages = pkg_resources.working_set
        packages_info = {pkg.key: pkg.version for pkg in installed_packages}
        logger.info(f"Installed packages: {packages_info}")
    except Exception as e:
        logger.error(f"Error listing installed packages: {str(e)}")
    logger.info("==== End of exit handler ====")


atexit.register(on_exit)

logger.info("==== Module Initialization: Start ====")
logger.info(f"All env vars at import: {dict(os.environ)}")
logger.info(
    f"SUPABASE_SERVICE_ROLE_KEY at import: {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}"
)
load_dotenv()
logger.info("Loaded .env file contents")
logger.info(f"All env vars after load_dotenv: {dict(os.environ)}")
logger.info(
    f"SUPABASE_SERVICE_ROLE_KEY after load_dotenv: {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}"
)
logger.info(f"Python version: {sys.version}")
try:
    installed_packages = pkg_resources.working_set
    packages_info = {pkg.key: pkg.version for pkg in installed_packages}
    logger.info(f"Installed packages at module init: {packages_info}")
except Exception as e:
    logger.error(f"Error listing installed packages at init: {str(e)}")
logger.info("==== Module Initialization: End ====")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==== Entering lifespan startup ====")
    logger.info("Attempting Supabase connection test during startup...")
    try:
        test_response = supabase.table("content").select("*").limit(1).execute()
        logger.info(f"Supabase connection test successful, data: {test_response.data}")
    except Exception as e:
        logger.error(f"Supabase test query failed during startup: {e}")

    try:
        logger.info("Initializing storage with init_storage()...")
        await init_storage(supabase)
        logger.info("Storage initialization completed successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize storage: {str(e)}")

    logger.info("Sleeping for 2 seconds to observe environment stability...")
    await asyncio.sleep(2)
    logger.info("Sleep complete, continuing lifespan startup.")
    logger.info("==== Yielding lifespan to allow request handling ====")
    yield
    logger.info("==== Entering lifespan shutdown ====")
    logger.info("==== Lifespan shutdown complete ====")


logger.info("Creating FastAPI app instance with lifespan handler...")
app = FastAPI(lifespan=lifespan)
logger.info("FastAPI app instance created.")
security = HTTPBearer()

logger.info("==== Pre-client creation environment checks ====")
logger.info(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
logger.info(
    f"SUPABASE_SERVICE_ROLE_KEY present: {'Yes' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'No'}"
)
logger.info(f"All env vars before client creation: {dict(os.environ)}")
logger.info("==== End of pre-client creation checks ====")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    logger.error(
        f"Missing required environment variables. URL present: {bool(supabase_url)}, Key present: {bool(supabase_key)}"
    )
    raise ValueError("Missing required Supabase environment variables")

logger.info("Creating global Supabase client instance...")
try:
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Global Supabase client instance created successfully.")
except Exception as e:
    logger.error(f"Failed to create global Supabase client: {e}")
    raise


# The rest of your FastAPI routes and functions remain unchanged...
def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> tuple[Client, dict]:
    logger.info("Entering authenticate() function.")
    try:
        logger.info(f"Received credentials with scheme: {credentials.scheme}")
        if credentials.scheme != "Bearer":
            raise ValueError("Invalid authorization scheme")
        logger.info(
            "Creating Supabase client within authenticate() with custom headers..."
        )
        auth_supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            options=ClientOptions(
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            ),
        )
        logger.info("Fetching user from Supabase auth...")
        user_response = auth_supabase.auth.get_user(credentials.credentials)
        if not user_response or not user_response.user:
            raise ValueError("User not found")
        logger.info(f"User authenticated successfully: {user_response.user}")
        return auth_supabase, user_response.user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Failed to authenticate")


@app.get("/")
async def root():
    logger.info("Received request at root endpoint.")
    return {"message": "PostOnce API is running"}


class ContentGenerationRequest(BaseModel):
    account_id: str
    content_id: str  # Add this
    post_id: Optional[str] = None
    content: Optional[str] = None
    content_type: Literal[
        "precta_tweet",
        "postcta_tweet",
        "thread_tweet",
        "long_form_tweet",
        "long_form_post",
        "image_list",
        "carousel_tweet",  # Add these two
        "carousel_post",
    ]

    def validate_request(self):
        """Validate that either post_id or content is provided, but not both."""
        if bool(self.post_id) == bool(self.content):
            raise ValueError("Exactly one of post_id or content must be provided")


@app.post("/generate_content")
async def generate_content_endpoint(
    request: ContentGenerationRequest,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    try:
        logger.info(f"Received request: {request}")

        # Validate request format
        request.validate_request()

        account_profile_service = AccountProfileService(client_user[0])
        logger.info(f"Fetching account profile for account_id: {request.account_id}")
        account_profile = await account_profile_service.get_account_profile(
            request.account_id
        )

        if not account_profile:
            logger.error(
                f"Account profile not found for account_id: {request.account_id}"
            )
            raise HTTPException(status_code=404, detail="Account profile not found")

        logger.info(f"Account profile found: {account_profile}")

        return StreamingResponse(
            content_generator(
                account_profile,
                request.content_id,  # Add this
                request.post_id,
                request.content_type,
                client_user[0],
                request.content,
            ),
            media_type="text/event-stream",
        )
    except ValueError as e:
        logger.error(f"Validation error in generate_content_endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in generate_content_endpoint: {str(e)}")
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
    status_service = StatusService(supabase)

    async def heartbeat():
        try:
            while True:
                await asyncio.sleep(5)
                heartbeat_message = {
                    "status": "heartbeat",
                    "message": "Still processing...",
                }
                logger.info(f"Sending heartbeat message: {heartbeat_message}")
                yield json.dumps(heartbeat_message) + "\n"
                logger.info("Sent heartbeat to keep connection alive")
        except asyncio.CancelledError:
            logger.info("Heartbeat cancelled")

    try:
        logger.info(
            f"Starting content generation for {'post_id: ' + post_id if post_id else 'pasted content'}"
        )
        start_message = {
            "status": "started",
            "message": "Initializing content generation and editing",
        }
        logger.info(f"Sending start message: {start_message}")
        yield json.dumps(start_message) + "\n"
        logger.info("Start message sent")
        await asyncio.sleep(0.1)

        # Run the main content generation process
        result = await run_main_process(
            account_profile,
            content_id,
            post_id,
            content_type,
            supabase,
            content,
        )
        logger.info(f"Result from run_main_process: {result}")

        if not isinstance(result, dict):
            logger.error(f"Invalid result format returned: {result}")
            await status_service.update_status(content_id, "failed")
            error_message = {
                "status": "failed",
                "error": "Invalid result format",
                "total_time": f"{time.time() - start_time:.2f} seconds",
            }
            logger.info(f"Sending error message for invalid format: {error_message}")
            yield json.dumps(error_message) + "\n"
            logger.info("Error message sent")
            return

        if result.get("success", False):
            logger.info(f"Content generation succeeded: {result}")
            await status_service.update_status(content_id, "generated")
            success_message = {
                "status": "completed",
                "result": result,
                "total_time": f"{time.time() - start_time:.2f} seconds",
            }
            logger.info(f"Sending success message: {success_message}")
            yield json.dumps(success_message) + "\n"
            logger.info("Success message sent")
        else:
            error_msg = result.get("error", "Unknown error during content generation")
            logger.error(f"Content generation failed: {error_msg}")
            await status_service.update_status(content_id, "failed")
            error_message = {
                "status": "failed",
                "error": error_msg,
                "total_time": f"{time.time() - start_time:.2f} seconds",
            }
            logger.info(f"Sending error message for failed generation: {error_message}")
            yield json.dumps(error_message) + "\n"
            logger.info("Error message sent")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in content generation process: {error_msg}")
        await status_service.update_status(content_id, "failed")
        exception_message = {
            "status": "failed",
            "error": error_msg,
            "total_time": f"{time.time() - start_time:.2f} seconds",
        }
        logger.info(f"Sending exception message: {exception_message}")
        yield json.dumps(exception_message) + "\n"
        logger.info("Exception message sent")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
