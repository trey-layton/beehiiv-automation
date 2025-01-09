import json
import asyncio
import time
import os
import sys
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

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for maximum verbosity
    format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add file handler for persistent logging
try:
    fh = logging.FileHandler("/tmp/fastapi_debug.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info("File logging handler successfully initialized")
except Exception as e:
    logger.error(f"Failed to initialize file logging handler: {str(e)}")

# Log system information
logger.info(f"Python version: {sys.version}")
logger.info(f"Python implementation: {sys.implementation}")
logger.info(f"Platform: {sys.platform}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Environment variables present: {list(os.environ.keys())}")

print("All env vars:", os.environ)
logger.debug("Environment variables dump complete")
print("Specific key:", os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
logger.debug("Specific key logging complete")

load_dotenv()
logger.info("Environment variables loaded from .env file")


def log_function_entry_exit(func):
    """Decorator to log function entry and exit"""

    async def wrapper(*args, **kwargs):
        logger.debug(f"Entering function: {func.__name__}")
        logger.debug(f"Arguments: args={args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Exiting function: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {str(e)}")
            logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            raise

    return wrapper


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "==================== ASGI STARTUP SEQUENCE BEGINNING ===================="
    )
    logger.debug("Lifespan context manager entered")

    # Log all current environment variables
    logger.debug("Environment variables at startup:")
    for key, value in os.environ.items():
        if "key" in key.lower() or "secret" in key.lower():
            logger.debug(f"{key}: [REDACTED]")
        else:
            logger.debug(f"{key}: {value}")

    try:
        logger.info("Testing Supabase client initialization...")
        logger.debug(
            f"Supabase URL availability: {'Yes' if os.getenv('SUPABASE_URL') else 'No'}"
        )
        logger.debug(
            f"Supabase key availability: {'Yes' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'No'}"
        )

        # Test Supabase connection
        logger.info("Attempting Supabase connection test...")
        try:
            test_response = supabase.table("content").select("*").limit(1).execute()
            logger.info("Supabase connection test successful")
            logger.debug(f"Test query response: {test_response}")
            logger.debug(f"Response data type: {type(test_response)}")
            logger.debug(
                f"Response status: {getattr(test_response, 'status_code', 'N/A')}"
            )
        except Exception as e:
            logger.error(f"Supabase connection test failed: {str(e)}")
            logger.error(
                f"Connection error traceback: {''.join(traceback.format_tb(e.__traceback__))}"
            )
            raise

        logger.info("Initializing storage...")
        try:
            await init_storage(supabase)
            logger.info("Storage initialization successful")
        except Exception as e:
            logger.error(f"Storage initialization error: {str(e)}")
            logger.error(
                f"Storage error traceback: {''.join(traceback.format_tb(e.__traceback__))}"
            )
            logger.warning("Continuing despite storage initialization failure")

        # Memory usage logging
        try:
            import psutil

            process = psutil.Process()
            logger.info(
                f"Memory usage at startup: {process.memory_info().rss / 1024 / 1024:.2f} MB"
            )
        except ImportError:
            logger.warning("psutil not available for memory logging")

        # Test async functionality
        logger.info("Testing async functionality...")
        try:
            await asyncio.sleep(0.1)
            logger.info("Async sleep test successful")
        except Exception as e:
            logger.error(f"Async functionality test failed: {str(e)}")

        logger.info(
            "==================== ASGI STARTUP SEQUENCE COMPLETED ===================="
        )
        logger.info("Application ready to handle requests")

        yield

        logger.info(
            "==================== ASGI SHUTDOWN SEQUENCE BEGINNING ===================="
        )
        logger.debug("Beginning shutdown sequence")

        # Cleanup logging
        try:
            logger.info("Performing cleanup operations...")
            # Add any cleanup code here
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Cleanup error during shutdown: {str(e)}")

        logger.info(
            "==================== ASGI SHUTDOWN SEQUENCE COMPLETED ===================="
        )

    except Exception as e:
        logger.critical(f"Critical error during lifespan: {str(e)}")
        logger.critical(
            f"Full traceback: {''.join(traceback.format_tb(e.__traceback__))}"
        )
        raise


app = FastAPI(lifespan=lifespan)
logger.info("FastAPI application instance created")

security = HTTPBearer()
logger.info("Security bearer initialized")

# Extensive environment logging
logger.info("Performing detailed environment check:")
logger.info(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
logger.info(
    f"SUPABASE_SERVICE_ROLE_KEY present: {'Yes' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'No'}"
)
logger.debug("Environment variables (sanitized):")
for key, value in os.environ.items():
    if "key" in key.lower() or "secret" in key.lower():
        logger.debug(f"{key}: [REDACTED]")
    else:
        logger.debug(f"{key}: {value}")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    logger.critical("Missing critical Supabase configuration")
    logger.error(
        f"URL present: {bool(supabase_url)}, Key present: {bool(supabase_key)}"
    )
    raise ValueError("Missing required Supabase environment variables")

logger.info("Creating global Supabase client...")
try:
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    )
    logger.info("Global Supabase client created successfully")
except Exception as e:
    logger.critical(f"Failed to create Supabase client: {str(e)}")
    raise


@log_function_entry_exit
async def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> tuple[Client, dict]:
    logger.debug(f"Authentication attempt with scheme: {credentials.scheme}")
    try:
        if credentials.scheme != "Bearer":
            logger.error(f"Invalid auth scheme: {credentials.scheme}")
            raise ValueError("Invalid authorization scheme")

        logger.debug("Creating authenticated Supabase client...")
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            options=ClientOptions(
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            ),
        )
        logger.debug("Authenticated Supabase client created")

        logger.debug("Attempting to get user...")
        user_response = supabase.auth.get_user(credentials.credentials)
        logger.debug(f"User response received: {bool(user_response)}")

        if not user_response or not user_response.user:
            logger.error("User not found in response")
            raise ValueError("User not found")

        logger.info(f"Authentication successful for user: {user_response.user.id}")
        return supabase, user_response.user
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        logger.error(
            f"Auth error traceback: {''.join(traceback.format_tb(e.__traceback__))}"
        )
        raise HTTPException(status_code=401, detail="Failed to authenticate")


@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
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
