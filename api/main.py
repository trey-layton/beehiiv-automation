from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Literal
from celery.result import AsyncResult
import os
import logging
from supabase import create_client, Client, ClientOptions
from ..celery_app import celery_app
from ..tasks import generate_content, test_redis
from core.services.account_profile_service import AccountProfileService

logger = logging.getLogger(__name__)

api_app = FastAPI()
security = HTTPBearer()


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


class ContentGenerationRequest(BaseModel):
    account_id: str
    post_id: str
    content_type: Literal[
        "precta_tweet", "postcta_tweet", "thread_tweet", "long_form_tweet", "linkedin"
    ]


@api_app.get("/")
async def root():
    return {"message": "PostOnce API is running"}


@api_app.post("/generate_content")
async def generate_content_endpoint(
    request: ContentGenerationRequest,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    try:
        account_profile_service = AccountProfileService(client_user[0])
        account_profile = await account_profile_service.get_account_profile(
            request.account_id
        )

        if not account_profile:
            raise HTTPException(status_code=404, detail="Account profile not found")

        task = generate_content.delay(
            account_profile.dict(), request.post_id, request.content_type
        )
        return {"task_id": task.id}
    except Exception as e:
        logger.exception(f"Unexpected error in generate_content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_app.get("/content_status/{task_id}")
async def get_content_status(
    task_id: str,
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        if task_result.state == "PENDING":
            return {"status": "processing"}
        elif task_result.state == "SUCCESS":
            return {"status": "success", "result": task_result.result}
        else:
            return {"status": "failed", "error": str(task_result.result)}
    except Exception as e:
        logger.exception(f"Error in get_content_status: {str(e)}")
        return {"status": "error", "message": str(e)}


@api_app.get("/test_redis")
async def test_redis_endpoint(
    client_user: tuple[Client, dict] = Depends(authenticate),
):
    task = test_redis.delay()
    return {"task_id": task.id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api_app, host="0.0.0.0", port=8000)
