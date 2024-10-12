from pydantic import ValidationError
from core.models.account_profile import AccountProfile
from supabase import Client
import logging

logger = logging.getLogger(__name__)


class AccountProfileService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def get_account_profile(self, account_profile: str):
        response = (
            self.supabase.table("account_profiles")
            .select("*")
            .eq("account_id", account_profile)
            .execute()
        )
        if response.data:
            try:
                return AccountProfile(**response.data[0])
            except ValidationError as e:
                raise ValueError("Incomplete account profile data")
        raise ValueError("Account profile not found")

    async def update_style_example(
        self, account_id: str, platform: str, style_example: str
    ):
        try:
            field_name = f"example_{platform.lower()}"
            response = (
                self.supabase.table("account_profiles")
                .update({field_name: style_example})
                .eq("account_id", account_id)
                .execute()
            )

            if response.data:
                return AccountProfile(**response.data[0])
            else:
                return None
        except Exception as e:
            logger.error(f"Error updating {platform} style example: {str(e)}")
            return None

    async def update_newsletter_content(self, account_id: str, content: str):
        try:
            response = (
                self.supabase.table("account_profiles")
                .update({"newsletter_content": content})
                .eq("account_id", account_id)
                .execute()
            )

            if response.data:
                return AccountProfile(**response.data[0])
            else:
                return None
        except Exception as e:
            logger.error(f"Error updating newsletter content: {str(e)}")
            return None
