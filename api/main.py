"""
PostOnce Backend API - Main FastAPI Application.

This module implements the primary REST API for PostOnce, a sophisticated content
automation platform that transforms newsletter content into engaging social media posts
using advanced AI processing.

Key Features:
- JWT-based authentication via Supabase
- Real-time content generation with Server-Sent Events streaming
- Comprehensive error handling and validation
- Support for multiple social media platforms (Twitter, LinkedIn)
- AI-powered content personalization and optimization
- Image processing and carousel generation
- Automatic status tracking and progress reporting

Architecture:
The API follows a clean layered architecture with clear separation of concerns:
- **API Layer**: FastAPI endpoints with authentication and validation
- **Business Logic**: Core processing pipeline in main_process module
- **Services**: Account management, status tracking, file storage
- **Models**: Pydantic data models for type safety and validation

Endpoints:
- `GET /`: Health check endpoint
- `POST /generate_content`: Main content generation with streaming response

Authentication:
All endpoints (except health check) require JWT Bearer token authentication.
Tokens are obtained through Supabase authentication and passed in the
Authorization header: "Bearer <jwt_token>"

Content Generation Pipeline:
The main endpoint orchestrates a sophisticated 7-step AI processing pipeline:
1. Content fetching from Beehiiv API or direct input
2. AI-powered structure analysis
3. Content strategy determination
4. Platform-specific content generation
5. Image relevance checking
6. Brand voice personalization
7. Hook writing and final optimization

Each step provides real-time status updates via Server-Sent Events, allowing
frontend applications to show progress and handle long-running operations gracefully.

Usage:
    # Start the application
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

    # Generate content via API
    POST /generate_content
    {
        "account_id": "user123",
        "content_id": "content456",
        "post_id": "beehiiv_post_789",
        "content_type": "thread_tweet"
    }

Environment Setup:
    - SUPABASE_URL: Supabase project URL
    - SUPABASE_SERVICE_ROLE_KEY: Service role key for admin operations
    - ANTHROPIC_API_KEY or OPENAI_API_KEY: AI provider credentials
    - Additional optional configuration variables

Deployment:
Optimized for Vercel serverless deployment with 5-minute execution limit
and 1GB memory allocation for AI processing operations.
"""

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
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from core.main_process import run_main_process
from core.services.status_updates import StatusService
from core.content.image_generation.carousel_generator import CarouselGenerator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

print("All env vars:", os.environ)
print("Specific key:", os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
logger = logging.getLogger(__name__)
load_dotenv()  # Force reload from .env


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing application...")
    try:
        await init_storage(supabase)
        logger.info("Storage initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize storage: {str(e)}")
        # We don't raise the exception here because we want the app to start
        # even if bucket creation fails - they might already exist

    yield

    # Shutdown
    logger.info("Shutting down application...")
    # Add any cleanup code here if needed


app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

logger.info("Environment check before client creation:")
logger.info(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
logger.info(
    f"SUPABASE_SERVICE_ROLE_KEY present: {'Yes' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'No'}"
)
logger.info(f"All env vars: {dict(os.environ)}")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    logger.error(
        f"Missing required environment variables. URL present: {bool(supabase_url)}, Key present: {bool(supabase_key)}"
    )
    raise ValueError("Missing required Supabase environment variables")

# Global setup - use service role key
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)


def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> tuple[Client, dict]:
    """
    Authenticate incoming API requests using JWT Bearer tokens.

    This function validates JWT tokens obtained from Supabase authentication
    and returns both a Supabase client configured for the authenticated user
    and the user information.

    Args:
        credentials: HTTP Bearer token credentials from request header

    Returns:
        Tuple containing:
        - Supabase client configured with user authentication
        - User object containing user information and metadata

    Raises:
        HTTPException: 401 Unauthorized if authentication fails

    Example:
        ```python
        @app.post("/protected-endpoint")
        async def protected(client_user: tuple = Depends(authenticate)):
            supabase_client, user = client_user
            # Use authenticated client for operations
        ```
    """
    try:
        if credentials.scheme != "Bearer":
            raise ValueError("Invalid authorization scheme")
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            options=ClientOptions(
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            ),
        )
        user_response = supabase.auth.get_user(credentials.credentials)
        if not user_response or not user_response.user:
            raise ValueError("User not found")
        return supabase, user_response.user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Failed to authenticate")


@app.get("/")
async def root():
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

    def validate_request(self) -> None:
        """
        Validate request parameters for content generation.

        Ensures that exactly one content source is provided (either post_id
        for Beehiiv content or direct content string) to prevent ambiguous
        content generation requests.

        Raises:
            ValueError: If both post_id and content are provided, or if neither is provided

        Example:
            ```python
            # Valid requests
            request1 = ContentGenerationRequest(
                account_id="user1", content_id="c1",
                post_id="beehiiv_123", content_type="thread_tweet"
            )

            request2 = ContentGenerationRequest(
                account_id="user1", content_id="c2",
                content="Direct newsletter content...", content_type="long_form_post"
            )

            # Invalid - both sources provided
            bad_request = ContentGenerationRequest(
                account_id="user1", content_id="c3",
                post_id="beehiiv_123", content="Also direct content",
                content_type="thread_tweet"
            )
            bad_request.validate_request()  # Raises ValueError
            ```
        """
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
