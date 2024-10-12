from pydantic import BaseModel
from typing import List, Dict, Optional


class ContentSegment(BaseModel):
    type: str
    content: str


class ContentStrategy(BaseModel):
    post_number: int
    section_title: str
    section_content: str


class Post(BaseModel):
    type: str
    content: str


class Content(BaseModel):
    provider: str
    type: str
    content: Dict[str, List[Post]]
    thumbnail_url: Optional[str] = None


class NewsletterStructure(BaseModel):
    sections: Dict[str, str]


#
