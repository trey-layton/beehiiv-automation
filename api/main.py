import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv
from core.main_process import run_main_process
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()


def get_access_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> str:
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization scheme"
        )
    return credentials.credentials


def get_supabase_client(access_token: str = Depends(get_access_token)) -> Client:
    try:
        return create_client(os.getenv("SUPABASE_URL"), access_token)
    except Exception as e:
        logger.error(f"Error creating Supabase client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/user_info")
async def get_user_data(supabase: Client = Depends(get_supabase_client)):
    try:
        response = supabase.from_("account_profiles").select("*").execute()

        if response.data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user data"
            )

        return response.data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user data: {str(e)}"
        )


class UserProfile(BaseModel):
    account_id: str
    beehiiv_api_key: str
    publication_id: str
    subscribe_url: str


@app.post("/update_user_profile")
async def update_user_profile(params: UserProfile, supabase: Client = Depends(get_supabase_client)):
    try:
        logger.info("Attempting to update profile")
        response = supabase.from_("account_profiles").upsert(
            {
                "account_id": params.account_id,
                "beehiiv_api_key": params.beehiiv_api_key,
                "publication_id": params.publication_id,
                "subscribe_url": params.subscribe_url,
            }
        ).execute()

        if response.data is None:
            logger.error("Failed to update profile: No data returned")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )

        logger.info("Profile updated successfully")
        return {
            "status": "success",
            "message": "Profile updated successfully",
            "data": response.data
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user profile: {str(e)}"
        )


class ContentGeneration(BaseModel):
    account_id: str
    edition_url: HttpUrl
    generate_precta_tweet: bool = False
    generate_postcta_tweet: bool = False
    generate_thread_tweet: bool = False
    generate_long_form_tweet: bool = False
    generate_linkedin: bool = False


@app.post("/generate_content")
async def generate_content(params: ContentGeneration, supabase: Client = Depends(get_supabase_client)):
    try:
        account_profile = supabase.from_("account_profiles").select("*").eq("account_id", params.account_id).execute()

        if account_profile.data is None:
            logger.warning("User profile not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please update your profile."
            )

        success, message, content = await run_main_process(
            account_profile.data[0],
            str(params.edition_url),
            params.generate_precta_tweet,
            params.generate_postcta_tweet,
            params.generate_thread_tweet,
            params.generate_long_form_tweet,
            params.generate_linkedin,
        )

        if success:
            logger.info("Content generated successfully")
            return {"status": "success", "message": message, "content": content}
        else:
            logger.warning(f"Content generation failed: {message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error in generate_content_endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating content: {str(e)}"
        )
