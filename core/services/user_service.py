from core.models.user import User
from fastapi import HTTPException
from supabase import Client


class UserService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def get_user_profile(self, user_id: str) -> User:
        response = (
            self.supabase.table("user_profiles").select("*").eq("id", user_id).execute()
        )
        if response.data:
            return User(**response.data[0])
        raise HTTPException(status_code=404, detail="User profile not found")

    # Add other user-related operations here
