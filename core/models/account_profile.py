from typing import Optional
from pydantic import BaseModel, Field


class AccountProfile(BaseModel):
    account_id: str
    beehiiv_api_key: str
    subscribe_url: str
    publication_id: str
    custom_prompt: str = Field(default="")
    example_tweet: Optional[str] = Field(default="")
    example_linkedin: Optional[str] = Field(default="")
    newsletter_content: Optional[str] = Field(default="")

    class Config:
        from_attributes = True
