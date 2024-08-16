from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Literal
from core.main_process import run_main_process
from supabase import create_client, Client, ClientOptions
import os
from core.services.account_profile_service import AccountProfileService
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()
security = HTTPBearer()


<<<<<<< HEAD
def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> tuple[Client, dict]:
=======
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
>>>>>>> feature/improved-llm-flow
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


class ContentGenerationRequest(BaseModel):
    account_id: str
    post_id: str
    content_type: Literal[
        'precta_tweet',
        'postcta_tweet',
        'thread_tweet',
        'long_form_tweet',
        'linkedin'
    ]

@app.get("/")
async def root():
    return {"message": "PostOnce API is running"}


@app.post("/generate_content")
async def generate_content(request: ContentGenerationRequest, client_user: tuple[Client, dict] = Depends(authenticate)):
    try:
        account_profile_service = AccountProfileService(client_user[0])
        account_profile = await account_profile_service.get_account_profile(request.account_id)
        success, message, generated_content = await run_main_process(
            account_profile,
            request.post_id,
            request.content_type
        )
<<<<<<< HEAD
        logger.info(
            f"run_main_process result: success={success}, message={message}, content={generated_content}"
=======
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
>>>>>>> feature/improved-llm-flow
        )

        if success:
            return {
                "status": "success",
                "message": message,
                "provider": generated_content["provider"],
                "type": generated_content["type"],
                "content": generated_content["content"]
            }
        else:
            logger.error(f"Error in run_main_process: {message}")
            raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        logger.exception(f"Unexpected error in generate_content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
