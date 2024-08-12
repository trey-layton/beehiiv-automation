from pydantic import BaseModel


class AccountProfile(BaseModel):
    account_id: str
    beehiiv_api_key: str
    subscribe_url: str
    publication_id: str

    class Config:
        from_attributes = True
