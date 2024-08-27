import json
import asyncio
import time
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Literal, AsyncGenerator
from core.content.content_fetcher import fetch_beehiiv_content
from core.content.improved_llm_flow.content_editor import edit_content
from supabase import create_client, Client, ClientOptions
from core.models.account_profile import AccountProfile
from core.services.account_profile_service import AccountProfileService
import logging
from dotenv import load_dotenv
from core.social_media.twitter.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweet,
    generate_long_form_tweet,
)
from core.social_media.linkedin.generate_linkedin_post import generate_linkedin_post
from core.content.image_generator import (
    generate_image_list_content,
    generate_image_list as generate_image,
)
from core.utils.storage_utils import upload_to_supabase

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
        "linkedin",
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
        account_profile = await account_profile_service.get_account_profile(
            request.account_id
        )

        if not account_profile:
            raise HTTPException(status_code=404, detail="Account profile not found")

        logger.info(f"Account profile found: {account_profile}")

        return StreamingResponse(
            content_generator(
                account_profile.dict(),
                request.post_id,
                request.content_type,
                client_user[0],
            ),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Error in generate_content_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def content_generator(
        account_profile: dict, post_id: str, content_type: str, supabase: Client
) -> AsyncGenerator[str, None]:
    start_time = time.time()

    async def heartbeat():
        while True:
            await asyncio.sleep(5)
            yield json.dumps(
                {"status": "heartbeat", "message": "Still processing..."}
            ) + "\n"

    heartbeat_task = None

    try:
        heartbeat_task = asyncio.create_task(heartbeat().__anext__())

        yield json.dumps(
            {"status": "started", "message": "Initializing content generation"}
        ) + "\n"
        await asyncio.sleep(0.1)

        logger.info("Content generation started")
        account_profile_obj = AccountProfile(**account_profile)

        yield json.dumps(
            {"status": "in_progress", "message": "Fetching content from Beehiiv"}
        ) + "\n"
        content_data = await fetch_beehiiv_content(
            account_profile_obj, post_id, supabase
        )
        yield json.dumps(
            {"status": "in_progress", "message": "Content fetched successfully"}
        ) + "\n"

        yield json.dumps(
            {"status": "in_progress", "message": "Generating initial content"}
        ) + "\n"

        if content_type == "image_list":
            yield json.dumps(
                {"status": "in_progress", "message": "Generating image list content"}
            ) + "\n"
            initial_content = await generate_image_list_content(
                content_data["free_content"], AccountProfile(**account_profile)
            )

            yield json.dumps(
                {"status": "in_progress", "message": "Generating image"}
            ) + "\n"
            try:
                image = generate_image(
                    initial_content,
                    save_locally=os.getenv("ENVIRONMENT") == "development",
                )

                yield json.dumps(
                    {"status": "in_progress", "message": "Uploading image to Supabase"}
                ) + "\n"
                file_name = f"image_list_{post_id}.png"
                image_url = upload_to_supabase(supabase, image, "images", file_name)
                # Add a timestamp to create a unique filename
                unique_id = f"{post_id}_{int(time.time() * 1000)}"  # Use milliseconds for more uniqueness
                file_name = f"image_list_{unique_id}.png"
                image_url = upload_to_supabase(supabase, image, "images", file_name)
                result = {
                    "provider": "twitter",
                    "type": "image_list",
                    "content": [
                        {
                            "type": "image",
                            "text": "",
                            "image_url": image_url,
                        }
                    ],
                    "thumbnail_url": content_data.get("thumbnail_url"),
                }
            except Exception as e:
                logger.error(f"Error in image generation or upload: {str(e)}")
                yield json.dumps(
                    {
                        "status": "failed",
                        "error": f"Error in image generation or upload: {str(e)}",
                    }
                ) + "\n"
                return
        else:
            if content_type == "precta_tweet":
                initial_content = await generate_precta_tweet(
                    content_data["free_content"], account_profile_obj
                )
            elif content_type == "postcta_tweet":
                initial_content = await generate_postcta_tweet(
                    content_data["free_content"],
                    account_profile_obj,
                    content_data["web_url"],
                )
            elif content_type == "thread_tweet":
                initial_content = await generate_thread_tweet(
                    content_data["free_content"],
                    content_data["web_url"],
                    account_profile_obj,
                )
            elif content_type == "long_form_tweet":
                initial_content = await generate_long_form_tweet(
                    content_data["free_content"], account_profile_obj
                )
            elif content_type == "linkedin":
                initial_content = await generate_linkedin_post(
                    content_data["free_content"], account_profile_obj
                )
            else:
                raise ValueError(f"Unsupported content type: {content_type}")

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

            if content_type in [
                "precta_tweet",
                "postcta_tweet",
                "thread_tweet",
                "long_form_tweet",
            ]:
                provider = "twitter"
            elif content_type == "linkedin":
                provider = "linkedin"
            else:
                provider = "unknown"
                logger.error(f"Unknown content type: {content_type}")

            result = {
                "provider": provider,
                "type": content_type,
                "content": edited_content,
                "thumbnail_url": content_data.get("thumbnail_url"),
            }

        yield json.dumps(
            {
                "status": "completed",
                "result": result,
                "total_time": f"{time.time() - start_time:.2f} seconds",
            }
        ) + "\n"

    except Exception as e:
        logger.error(f"Error in content_generator: {str(e)}")
        yield json.dumps({"status": "failed", "error": str(e)}) + "\n"
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()

    logger.info("Content generation completed")
