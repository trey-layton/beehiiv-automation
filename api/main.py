import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv
from core.main_process import run_main_process
import logging
from tasks import generate_content_task
from celery.result import AsyncResult

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Create a single Supabase client instance using environment variables
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY environment variable is missing")

    supabase_client = create_client(supabase_url, supabase_key)
    logger.debug("Supabase client created successfully")
except Exception as e:
    logger.error(f"Error creating Supabase client: {str(e)}")
    raise


def get_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> str:
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization scheme",
        )
    return credentials.credentials


def get_supabase_client() -> Client:
    return supabase_client


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Received request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Returning response: Status {response.status_code}")
    return response


@app.get("/")
async def root():
    logger.debug("Root endpoint called")
    return {"message": "Hello World"}


@app.get("/test-supabase")
async def test_supabase(client: Client = Depends(get_supabase_client)):
    logger.debug("Test-supabase endpoint called")
    try:
        logger.debug("Attempting to query Supabase")
        response = client.table("user_profiles").select("*").limit(1).execute()
        logger.debug(f"Supabase response: {response}")
        return {"status": "success", "data": response.data}
    except Exception as e:
        logger.error(f"Supabase query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Supabase query failed: {str(e)}")


@app.get("/debug")
async def debug_info():
    logger.debug("Debug endpoint called")
    return {
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_key_length": (
            len(os.getenv("SUPABASE_KEY", "")) if os.getenv("SUPABASE_KEY") else 0
        ),
        "endpoints": [route.path for route in app.routes],
    }


@app.get("/user_info")
async def get_user_data(supabase: Client = Depends(get_supabase_client)):
    try:
        response = supabase.from_("account_profiles").select("*").execute()

        if response.data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user data",
            )

        return response.data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user data: {str(e)}",
        )


class UserProfile(BaseModel):
    account_id: str
    beehiiv_api_key: str
    publication_id: str
    subscribe_url: str


@app.post("/update_user_profile")
async def update_user_profile(
    params: UserProfile, supabase: Client = Depends(get_supabase_client)
):
    try:
        logger.info("Attempting to update profile")
        response = (
            supabase.from_("account_profiles")
            .upsert(
                {
                    "account_id": params.account_id,
                    "beehiiv_api_key": params.beehiiv_api_key,
                    "publication_id": params.publication_id,
                    "subscribe_url": params.subscribe_url,
                }
            )
            .execute()
        )

        if response.data is None:
            logger.error("Failed to update profile: No data returned")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile",
            )

        logger.info("Profile updated successfully")
        return {
            "status": "success",
            "message": "Profile updated successfully",
            "data": response.data,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user profile: {str(e)}",
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
async def generate_content(
    params: ContentGeneration, supabase: Client = Depends(get_supabase_client)
):
    try:
        account_profile = (
            supabase.from_("account_profiles")
            .select("*")
            .eq("account_id", params.account_id)
            .execute()
        )

        if account_profile.data is None:
            logger.warning("User profile not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please update your profile.",
            )

        task = generate_content_task.delay(
            account_profile.data[0],
            str(params.edition_url),
            params.generate_precta_tweet,
            params.generate_postcta_tweet,
            params.generate_thread_tweet,
            params.generate_long_form_tweet,
            params.generate_linkedin,
        )

        logger.info(f"Content generation task initiated: {task.id}")
        return {"status": "processing", "task_id": str(task.id)}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error in generate_content_endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating content generation: {str(e)}",
        )


@app.get("/task_status/{task_id}")
async def task_status(task_id: str):
    task = AsyncResult(task_id)
    if task.state == "PENDING":
        response = {"state": task.state, "status": "Task is pending..."}
    elif task.state != "FAILURE":
        response = {"state": task.state, "status": "Task is in progress..."}
        if task.info:
            response["result"] = task.info
    else:
        response = {
            "state": task.state,
            "status": "Task failed",
            "error": str(task.info),
        }
    return response
