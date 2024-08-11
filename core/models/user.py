from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    id: str
    email: str
    beehiiv_api_key: Optional[str] = None
    subscribe_url: Optional[str] = None
    publication_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True
