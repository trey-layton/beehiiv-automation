from pydantic import BaseModel


class AccountProfile(BaseModel):
    account_id: str
    beehiiv_api_key: str
    publication_id: str
    subscribe_url: str
    custom_prompt: str = ""

    class Config:
        from_attributes = True
