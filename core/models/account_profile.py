from pydantic import BaseModel, Field


class AccountProfile(BaseModel):
    account_id: str
    beehiiv_api_key: str
    subscribe_url: str
    publication_id: str
    custom_prompt: str = Field(default="")

    class Config:
        from_attributes = True
