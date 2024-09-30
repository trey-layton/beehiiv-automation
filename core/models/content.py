from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ContentSegment(BaseModel):
    type: str
    content: str


class Post(BaseModel):
    post_number: int
    segments: List[ContentSegment]


class Content(BaseModel):
    posts: List[Post]
    original_content: str
    content_type: str
    account_id: str
    metadata: Dict[str, Any] = {}


class ContentGenerationRequest(BaseModel):
    account_id: str
    post_id: str
    content_type: str
