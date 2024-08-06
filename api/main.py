import os
from typing import Any, Dict
import httpx
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client, Client
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv
from core.main_process import run_main_process
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
security = HTTPBearer()
supabase: Client = create_client(
    supabase_url=os.getenv("SUPABASE_URL"), supabase_key=os.getenv("SUPABASE_KEY")
)


class BeehiivConnection(BaseModel):
    beehiiv_api_key: str
    publication_id: str
    subscribe_url: str


class UserProfile(BaseModel):
    beehiiv_api_key: str
    publication_id: str
    subscribe_url: str


class ContentGeneration(BaseModel):
    edition_url: HttpUrl
    generate_precta_tweet: bool = False
    generate_postcta_tweet: bool = False
    generate_thread_tweet: bool = False
    generate_long_form_tweet: bool = False
    generate_linkedin: bool = False


async def get_user_profile(user_id: str) -> Dict[str, Any]:
    try:
        response = (
            supabase.table("user_profiles").select("*").eq("id", user_id).execute()
        )
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    try:
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        return user.user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )


@app.get("/user_info")
async def get_user_info(user: dict = Depends(get_current_user)):
    try:
        logger.info(f"Attempting to fetch info for user ID: {user.id}")

        url = (
            f"{os.getenv('SUPABASE_URL')}/rest/v1/accounts?select=email&id=eq.{user.id}"
        )
        headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {user.session.access_token if hasattr(user, 'session') else os.getenv('SUPABASE_KEY')}",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data:
                return {"email": data[0]["email"]}

        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/update_user_profile")
async def update_user_profile(
    profile: UserProfile, user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Attempting to update profile for user {user.id}")

        response = (
            supabase.table("user_profiles")
            .upsert(
                {
                    "id": user.id,
                    "beehiiv_api_key": profile.beehiiv_api_key,
                    "publication_id": profile.publication_id,
                    "subscribe_url": profile.subscribe_url,
                }
            )
            .execute()
        )

        if response.data:
            logger.info(f"Profile updated successfully for user {user.id}")
            return {
                "status": "success",
                "message": "Profile updated successfully",
                "data": response.data[0],
            }
        else:
            logger.error(f"No data returned when updating profile for user {user.id}")
            raise HTTPException(status_code=400, detail="Failed to update profile")

    except Exception as e:
        logger.error(f"Error updating profile for user {user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_content", response_model=Dict[str, Any])
async def generate_content_endpoint(
    params: ContentGeneration, current_user: dict = Depends(get_current_user)
):
    logger.info(f"generate_content_endpoint called for user {current_user.id}")
    try:
        user_profile = await get_user_profile(current_user.id)

        user_config = {
            "id": current_user.id,
            "subscribe_url": user_profile.get("subscribe_url"),
            "beehiiv_api_key": user_profile.get("beehiiv_api_key"),
            "publication_id": user_profile.get("publication_id"),
            # Add any other necessary user configuration here
        }

        success, message, content = await run_main_process(
            user_config,
            params.edition_url,
            params.generate_precta_tweet,
            params.generate_postcta_tweet,
            params.generate_thread_tweet,
            params.generate_long_form_tweet,
            params.generate_linkedin,
        )

        if success:
            logger.info(f"Content generated successfully for user {current_user.id}")
            return {"status": "success", "message": message, "content": content}
        else:
            logger.warning(
                f"Content generation failed for user {current_user.id}: {message}"
            )
            return {"status": "error", "message": message}
    except Exception as e:
        logger.exception(f"Error in generate_content_endpoint: {str(e)}")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
