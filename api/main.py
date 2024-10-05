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
from core.llm_steps.structure_analysis import analyze_structure
from core.llm_steps.content_strategy import determine_content_strategy
from core.llm_steps.content_generator import generate_content
from core.content.content_type_loader import get_instructions_for_content_type
from core.models.content import Content, Post, ContentSegment

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


def content_to_dict(content: Content) -> dict:
    return {
        "segments": [segment.dict() for segment in content.segments],
        "strategy": [strategy.dict() for strategy in content.strategy],
        "posts": [post.dict() for post in content.posts],
        "original_content": content.original_content,
        "content_type": content.content_type,
        "account_id": content.account_id,
        "metadata": content.metadata,
    }


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
            {
                "status": "in_progress",
                "message": "Content fetched successfully",
                "data": content_data,
            }
        ) + "\n"

        yield json.dumps(
            {"status": "in_progress", "message": "Analyzing content structure"}
        ) + "\n"
        structured_content = await analyze_structure(content_data["free_content"])
        yield json.dumps(
            {
                "status": "in_progress",
                "message": "Content structure analyzed",
                "data": [segment.dict() for segment in structured_content],
            }
        ) + "\n"

        yield json.dumps(
            {"status": "in_progress", "message": "Determining content strategy"}
        ) + "\n"
        content_strategy = await determine_content_strategy(structured_content)
        yield json.dumps(
            {
                "status": "in_progress",
                "message": "Content strategy determined",
                "data": [strategy.dict() for strategy in content_strategy],
            }
        ) + "\n"

        initial_content = Content(
            segments=structured_content,
            strategy=content_strategy,
            posts=[],
            original_content=content_data["free_content"],
            content_type=content_type,
            account_id=account_profile_obj.account_id,
            metadata={"web_url": content_data["web_url"], "post_id": post_id},
        )

        instructions = get_instructions_for_content_type(content_type)

        yield json.dumps(
            {"status": "in_progress", "message": "Generating content"}
        ) + "\n"
        generated_content = await generate_content(
            initial_content,
            instructions,
            account_profile_obj,
            supabase,
            save_locally=os.getenv("ENVIRONMENT") == "development",
        )
        yield json.dumps(
            {
                "status": "in_progress",
                "message": "Content generated",
                "data": content_to_dict(generated_content),
            }
        ) + "\n"

        if content_type != "image_list":
            yield json.dumps(
                {"status": "in_progress", "message": "Editing and refining content"}
            ) + "\n"
            edited_content = await edit_content(generated_content, content_type)
            yield json.dumps(
                {
                    "status": "in_progress",
                    "message": "Content editing completed",
                    "data": content_to_dict(edited_content),
                }
            ) + "\n"
        else:
            edited_content = generated_content

        provider = (
            "twitter"
            if content_type.endswith("tweet") or content_type == "image_list"
            else "linkedin"
        )

        result = {
            "provider": provider,
            "type": content_type,
            "content": content_to_dict(edited_content),
            "thumbnail_url": content_data.get("thumbnail_url"),
        }

        if content_type == "image_list":
            image_url = (
                edited_content.posts[0].metadata.get("image_url")
                if edited_content.posts
                else None
            )
            if image_url:
                result["image_url"] = image_url

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
