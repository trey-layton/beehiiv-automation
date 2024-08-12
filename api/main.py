from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
from typing import Dict, Union, List
from core.main_process import run_main_process
from supabase import create_client, Client
import os
from core.services.account_profile_service import AccountProfileService
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()
security = HTTPBearer()


def authenticate(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> tuple[Client, dict]:
    try:
        if credentials.scheme != "Bearer":
            raise ValueError("Invalid authorization scheme")

        supabase = create_client(os.getenv("SUPABASE_URL"), credentials.credentials)

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


@app.get("/")
async def root():
    return {"message": "PostOnce API is running"}


@app.post("/generate_content", response_model=ContentGenerationResponse)
async def generate_content(request: ContentGenerationRequest, client_user: tuple[Client, dict] = Depends(authenticate)):

    try:
        account_profile_service = AccountProfileService(client_user[0])
        account_profile = await account_profile_service.get_account_profile(request.account_id)

        success, message, generated_content = await run_main_process(
            account_profile,
            str(request.edition_url),
            request.generate_precta_tweet,
            request.generate_postcta_tweet,
            request.generate_thread_tweet,
            request.generate_long_form_tweet,
            request.generate_linkedin,
        )
        logger.info(
            f"run_main_process result: success={success}, message={message}, content={generated_content}"
        )

        if success:
            return ContentGenerationResponse(
                status="success", message=message, content=generated_content
            )
        else:
            logger.error(f"Error in run_main_process: {message}")
            raise HTTPException(status_code=500, detail=message)
    except Exception as e:
        logger.exception(f"Unexpected error in generate_content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
