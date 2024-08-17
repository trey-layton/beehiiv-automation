from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Literal, Dict, Any
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


def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
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


class ContentGenerationRequest(BaseModel):
    account_id: str
    post_id: str
    content_type: Literal[
        "precta_tweet", "postcta_tweet", "thread_tweet", "long_form_tweet", "linkedin"
    ]


@app.post("/generate_content")
async def generate_content(
    request: ContentGenerationRequest,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    logger.info(f"Received request: {request}")
    try:
        # Step 1: Authentication
        logger.info("Authenticating user")
        supabase_client, user = client_user
        logger.info(f"User authenticated: {user.id}")
        account_profile_service = AccountProfileService(supabase_client)
        account_profile = await account_profile_service.get_account_profile(
            request.account_id
        )

        success, message, generated_content = await run_main_process(
            account_profile, request.post_id, request.content_type
        )

        logger.info(
            f"run_main_process result: success={success}, message={message}, content={generated_content}"
        )

        if success:
            return {
                "status": "success",
                "message": message,
                "provider": generated_content["provider"],
                "type": generated_content["type"],
                "content": generated_content["content"],
            }
        else:
            logger.error(f"Error in run_main_process: {message}")
            raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        logger.exception(f"Unexpected error in generate_content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
