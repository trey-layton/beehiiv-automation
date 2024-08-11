from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
from typing import Dict, Union, List
from core.main_process import run_main_process

app = FastAPI()
security = HTTPBearer()


class ContentGenerationRequest(BaseModel):
    account_id: str
    edition_url: HttpUrl
    beehiiv_api_key: str
    publication_id: str
    subscribe_url: str
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
async def generate_content(
    request: ContentGenerationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        user_profile = {
            "id": request.account_id,
            "beehiiv_api_key": request.beehiiv_api_key,
            "publication_id": request.publication_id,
            "subscribe_url": request.subscribe_url,
        }

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
