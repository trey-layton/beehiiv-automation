from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ContentSegment(BaseModel):
    type: str
    content: str


class ContentStrategy(BaseModel):
    post_number: int
    section_type: str
    content: str
    strategy_note: str = ""


class Post(BaseModel):
    post_number: int
    section_type: str
    content: str
    metadata: Dict[str, Any] = {}


class Content(BaseModel):
    segments: Optional[List[ContentSegment]] = []
    strategy: Optional[List[ContentStrategy]] = []
    posts: List[Post]
    original_content: str
    content_type: str
    account_id: str
    metadata: Dict[str, Any] = {}
