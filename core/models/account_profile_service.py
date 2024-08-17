from pydantic import ValidationError
from core.models.account_profile import AccountProfile
from supabase import Client


class AccountProfileService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def get_account_profile(self, account_id: str):
        response = (
            self.supabase.table("account_profiles")
            .select("*")
            .eq("account_id", account_id)
            .execute()
        )
        if response.data:
            try:
                return AccountProfile(**response.data[0])
            except ValidationError as e:
                raise ValueError("Incomplete account profile data")
        raise ValueError("Account profile not found")
