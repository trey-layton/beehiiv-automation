import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from pydantic import BaseModel, HttpUrl, ConfigDict
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


def get_supabase_client() -> Client:
    return supabase_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    try:
        user = supabase_client.auth.get_user(credentials.credentials)
        return user.user
    except Exception as e:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )


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
        response = client.table("account_profiles").select("*").limit(1).execute()
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
async def get_user_info(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    try:
        logger.info(f"Fetching info for user ID: {current_user.id}")
        response = (
            supabase.table("account_profiles")
            .select("*")
            .eq("account_id", current_user.id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            user_profile = response.data[0]
            return {
                "account_id": user_profile["account_id"],
                "email": current_user.email,
                "beehiiv_api_key": user_profile["beehiiv_api_key"],
                "subscribe_url": user_profile["subscribe_url"],
                "publication_id": user_profile["publication_id"],
                "example_tweet": user_profile.get("example_tweet"),
            }
        else:
            raise HTTPException(status_code=404, detail="User profile not found")

    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


class UserProfile(BaseModel):
    beehiiv_api_key: str
    publication_id: str
    subscribe_url: str
    model_config = ConfigDict(from_attributes=True)


@app.post("/update_user_profile")
async def update_user_profile(
    params: UserProfile,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    try:
        logger.info("Attempting to update profile")
        response = (
            supabase.table("account_profiles")
            .upsert(
                {
                    "account_id": current_user.id,
                    "beehiiv_api_key": params.beehiiv_api_key,
                    "publication_id": params.publication_id,
                    "subscribe_url": params.subscribe_url,
                }
            )
            .execute()
        )

        if response.data is None:
            logger.error("Failed to update profile: No data returned")
            raise HTTPException(status_code=400, detail="Failed to update profile")

        logger.info("Profile updated successfully")
        return {
            "status": "success",
            "message": "Profile updated successfully",
            "data": response.data[0],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating user profile: {str(e)}"
        )


class ContentGeneration(BaseModel):
    edition_url: HttpUrl
    generate_precta_tweet: bool = False
    generate_postcta_tweet: bool = False
    generate_thread_tweet: bool = False
    generate_long_form_tweet: bool = False
    generate_linkedin: bool = False
    model_config = ConfigDict(from_attributes=True)


@app.post("/generate_content")
async def generate_content(
    params: ContentGeneration,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    try:
        logger.info(f"Generating content for user ID: {current_user.id}")
        logger.info(f"Params: {params}")

        # Fetch the account profile
        account_profile_response = (
            supabase.table("account_profiles")
            .select("*")
            .eq("account_id", current_user.id)
            .execute()
        )

        logger.info(f"Account profile response: {account_profile_response}")

        if not account_profile_response.data:
            logger.error(f"No profile found for user ID: {current_user.id}")
            raise HTTPException(
                status_code=404,
                detail="User profile not found. This is unexpected as the profile should exist.",
            )

        account_profile = account_profile_response.data[0]
        logger.info(f"Account profile data: {account_profile}")

        # Check if required fields are present
        required_fields = ["beehiiv_api_key", "publication_id", "subscribe_url"]
        missing_fields = [
            field for field in required_fields if not account_profile.get(field)
        ]

        if missing_fields:
            logger.warning(
                f"Incomplete profile for user ID: {current_user.id}. Missing fields: {missing_fields}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Incomplete user profile. Please update your profile with the following information: {', '.join(missing_fields)}",
            )

        # Initiate the content generation task
        task = generate_content_task.delay(
            account_profile,
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
        logger.error(f"HTTP exception in generate_content: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error in generate_content: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error initiating content generation: {str(e)}"
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
