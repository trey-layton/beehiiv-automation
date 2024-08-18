from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Literal
from core.main_process import run_main_process
from supabase import create_client, Client, ClientOptions
import os
from core.services.account_profile_service import AccountProfileService
from tasks import generate_content_task
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


@app.get("/")
async def root():
    return {"message": "PostOnce API is running"}


from tasks import generate_content_task


@app.post("/generate_content")
async def generate_content(
    request: ContentGenerationRequest,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    try:
        account_profile_service = AccountProfileService(client_user[0])
        account_profile = await account_profile_service.get_account_profile(
            request.account_id
        )

        # Convert AccountProfile to dict for serialization
        account_profile_dict = account_profile.dict()

        task = generate_content_task.delay(
            account_profile_dict, request.post_id, request.content_type
        )

        return {
            "status": "success",
            "message": "Content generation task submitted successfully",
            "task_id": task.id,
        }
    except Exception as e:
        logger.exception(f"Unexpected error in generate_content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task_status/{task_id}")
async def task_status(task_id: str):
    task = generate_content_task.AsyncResult(task_id)
    if task.state == "PENDING":
        response = {"state": task.state, "status": "Task is waiting for execution"}
    elif task.state != "FAILURE":
        response = {"state": task.state, "status": task.info.get("status", "")}
        if "result" in task.info:
            response["result"] = task.info["result"]
    else:
        response = {"state": task.state, "status": str(task.info)}
    return response
