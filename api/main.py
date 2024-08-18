from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Literal
from core.main_process import run_main_process
from supabase import create_client, Client, ClientOptions
import os
from core.services.account_profile_service import AccountProfileService
import logging
from dotenv import load_dotenv
from starlette.background import BackgroundTask
import asyncio

logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()
security = HTTPBearer()


async def authenticate(
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

        user_response = await supabase.auth.get_user(credentials.credentials)

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


@app.get("/")
async def root():
    return {"message": "PostOnce API is running"}


@app.post("/generate_content")
async def generate_content(
    request: Request,
    content_request: ContentGenerationRequest,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    async def process_content():
        try:
            account_profile_service = AccountProfileService(client_user[0])
            account_profile = await account_profile_service.get_account_profile(
                content_request.account_id
            )
            success, message, generated_content = await run_main_process(
                account_profile, content_request.post_id, content_request.content_type
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

    background_task = BackgroundTask(process_content)
    return {"message": "Content generation started"}, background_task
