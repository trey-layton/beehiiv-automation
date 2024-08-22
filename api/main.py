import json
import asyncio
import time
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Literal, AsyncGenerator
from core.content.content_fetcher import fetch_beehiiv_content
from core.content.improved_llm_flow.content_editor import edit_content
from supabase import create_client, Client, ClientOptions
import os
from core.models.account_profile import AccountProfile
from core.services.account_profile_service import AccountProfileService
import logging
from dotenv import load_dotenv

from core.social_media.twitter.generate_tweets import generate_thread_tweet

logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()
security = HTTPBearer()


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
        "precta_tweet", "postcta_tweet", "thread_tweet", "long_form_tweet", "linkedin"
    ]


@app.post("/generate_content")
async def generate_content_endpoint(
    request: ContentGenerationRequest,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    try:
        print("Received request:", request)
        account_profile_service = AccountProfileService(client_user[0])
        account_profile = await account_profile_service.get_account_profile(
            request.account_id
        )

        if not account_profile:
            raise HTTPException(status_code=404, detail="Account profile not found")

        print("Account profile found:", account_profile)

        return StreamingResponse(
            content_generator(
                account_profile.dict(), request.post_id, request.content_type
            ),
            media_type="text/event-stream",
        )
    except Exception as e:
        print("Error in generate_content_endpoint:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def content_generator(
    account_profile: dict, post_id: str, content_type: str
) -> AsyncGenerator[str, None]:
    start_time = time.time()
    try:
        yield json.dumps(
            {"status": "started", "message": "Initializing content generation"}
        ) + "\n"
        await asyncio.sleep(0.1)

        print("Content generation started")
        account_profile_obj = AccountProfile(**account_profile)

        yield json.dumps(
            {"status": "in_progress", "message": "Fetching content from Beehiiv"}
        ) + "\n"
        content_data = await fetch_beehiiv_content(account_profile_obj, post_id)
        yield json.dumps(
            {"status": "in_progress", "message": "Content fetched successfully"}
        ) + "\n"

        yield json.dumps(
            {"status": "in_progress", "message": "Generating initial content"}
        ) + "\n"
        if content_type == "thread_tweet":
            initial_content = await generate_thread_tweet(
                content_data["free_content"],
                content_data["web_url"],
                account_profile_obj,
            )
        # Add other content types here...

        yield json.dumps(
            {"status": "in_progress", "message": "Initial content generated"}
        ) + "\n"

        yield json.dumps(
            {"status": "in_progress", "message": "Editing and refining content"}
        ) + "\n"
        edited_content = await edit_content(initial_content, content_type)

        yield json.dumps(
            {"status": "in_progress", "message": "Content editing completed"}
        ) + "\n"

        result = {
            "provider": "twitter",
            "type": content_type,
            "content": edited_content,
        }

        for i, tweet in enumerate(edited_content):
            yield json.dumps(
                {
                    "status": "in_progress",
                    "message": f"Preparing tweet {i+1} of {len(edited_content)}",
                    "tweet": tweet,
                }
            ) + "\n"
            await asyncio.sleep(0.1)

        total_time = time.time() - start_time
        yield json.dumps(
            {
                "status": "completed",
                "result": result,
                "total_time": f"{total_time:.2f} seconds",
            }
        ) + "\n"
        print("Content generation completed")
        yield json.dumps(
            {
                "status": "completed",
                "result": result,
                "total_time": f"{total_time:.2f} seconds",
            }
        ) + "\n"
        await asyncio.sleep(
            0.5
        )  # Add a small delay to ensure the client receives the last message

    except Exception as e:
        print("Error in content_generator:", str(e))
        yield json.dumps({"status": "failed", "error": str(e)}) + "\n"

    async def heartbeat():
        while True:
            await asyncio.sleep(5)  # Send a heartbeat every 5 seconds
            yield json.dumps(
                {"status": "heartbeat", "message": "Still processing..."}
            ) + "\n"

    # Run the heartbeat concurrently with the main process
    asyncio.create_task(heartbeat())
