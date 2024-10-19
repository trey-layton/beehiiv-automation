import json
import asyncio
import time
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Literal
from supabase import create_client, Client, ClientOptions
from core.models.account_profile import AccountProfile
from core.services.account_profile_service import AccountProfileService
import logging
from dotenv import load_dotenv
from core.main_process import run_main_process

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()
security = HTTPBearer()

# Initialize Supabase client
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> tuple[Client, dict]:
    try:
        if credentials.scheme != "Bearer":
            raise ValueError("Invalid authorization scheme")

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY"),
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate",
        )


@app.get("/")
async def root():
    return {"message": "PostOnce API is running"}


class ContentGenerationRequest(BaseModel):
    account_id: str
    post_id: str
    content_type: Literal[
        "precta_tweet",
        "postcta_tweet",
        "thread_tweet",
        "long_form_tweet",
        "long_form_post",
        "image_list",
    ]


@app.post("/generate_content")
async def generate_content_endpoint(
    request: ContentGenerationRequest,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    try:
        logger.info(f"Received request: {request}")
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
                account_profile, request.post_id, request.content_type, client_user[0]
            ),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Error in generate_content_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def content_generator(
    account_profile: AccountProfile, post_id: str, content_type: str, supabase: Client
):
    start_time = time.time()

    async def heartbeat():
        try:
            while True:
                await asyncio.sleep(5)
                yield json.dumps(
                    {"status": "heartbeat", "message": "Still processing..."}
                ) + "\n"
                logger.info("Sent heartbeat to keep connection alive")
        except asyncio.CancelledError:
            logger.info("Heartbeat cancelled")

    # Start streaming the response
    try:
        logger.info(f"Starting content generation for post_id: {post_id}")
        yield json.dumps(
            {
                "status": "started",
                "message": "Initializing content generation and editing",
            }
        ) + "\n"
        await asyncio.sleep(0.1)

        # Run the main content generation process
        result = await run_main_process(
            account_profile, post_id, content_type, supabase
        )
        logger.info(f"Result from run_main_process: {result}")

        # Validate the result format
        if not isinstance(result, dict):
            logger.error(f"Invalid result format returned: {result}")
            yield json.dumps(
                {
                    "status": "failed",
                    "error": "Invalid result format",
                    "total_time": f"{time.time() - start_time:.2f} seconds",
                }
            ) + "\n"
            return

        # Check if content generation was successful
        if result.get("success", False):
            logger.info(f"Content generation succeeded: {result}")

            # Log the final result before yielding
            logger.info(f"Final result that will be sent to client: {result}")
            print(f"Final result being sent to client: {result}")

            yield json.dumps(
                {
                    "status": "completed",
                    "result": result,
                    "total_time": f"{time.time() - start_time:.2f} seconds",
                }
            ) + "\n"
        else:
            logger.error(f"Content generation failed: {result}")
            yield json.dumps(
                {
                    "status": "failed",
                    "error": result.get(
                        "error", "Unknown error during content generation"
                    ),
                    "total_time": f"{time.time() - start_time:.2f} seconds",
                }
            ) + "\n"

    except Exception as e:
        logger.error(f"Error in content generation or editing process: {str(e)}")
        yield json.dumps({"status": "failed", "error": str(e)}) + "\n"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
