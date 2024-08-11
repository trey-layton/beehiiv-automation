from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
from typing import Dict, Union, List
from core.main_process import run_main_process
from supabase import create_client, Client
import os
from cachetools import TTLCache
from datetime import timedelta

app = FastAPI()
security = HTTPBearer()

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=os.environ.get("SUPABASE_URL"),
    supabase_key=os.environ.get("SUPABASE_KEY"),
)

# Create a cache for user profiles
user_profile_cache = TTLCache(maxsize=1000, ttl=timedelta(minutes=15).total_seconds())


class ContentGenerationRequest(BaseModel):
    edition_url: HttpUrl
    generate_precta_tweet: bool = False
    generate_postcta_tweet: bool = False
    generate_thread_tweet: bool = False
    generate_long_form_tweet: bool = False
    generate_linkedin: bool = False


class ContentItem(BaseModel):
    type: str
    text: str


class ContentGenerationResponse(BaseModel):
    status: str
    message: str
    content: Dict[str, Union[str, List[ContentItem]]]


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Verify the token with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_user_profile(user_id: str):
    if user_id in user_profile_cache:
        return user_profile_cache[user_id]

    response = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
    if response.data:
        user_profile = response.data[0]
        user_profile_cache[user_id] = user_profile
        return user_profile
    raise HTTPException(status_code=404, detail="User profile not found")


@app.get("/")
async def root():
    return {"message": "PostOnce API is running"}


@app.post("/generate_content", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest, user: dict = Depends(verify_token)
):
    try:
        user_profile = await get_user_profile(user.id)

        success, message, generated_content = await run_main_process(
            user_profile,
            str(request.edition_url),
            request.generate_precta_tweet,
            request.generate_postcta_tweet,
            request.generate_thread_tweet,
            request.generate_long_form_tweet,
            request.generate_linkedin,
        )

        if success:
            return ContentGenerationResponse(
                status="success", message=message, content=generated_content
            )
        else:
            raise HTTPException(status_code=500, detail=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
