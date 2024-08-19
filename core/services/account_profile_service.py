# core/services/account_profile_service.py
from pydantic import ValidationError
from core.models.account_profile import AccountProfile
from fastapi import HTTPException
from supabase import Client
import logging

logger = logging.getLogger(__name__)


class AccountProfileService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def get_account_profile(self, account_id: str):
        try:
            logger.info(f"Fetching account profile for account_id: {account_id}")
            response = (
                self.supabase.table("account_profiles")
                .select("*")
                .eq("account_id", account_id)
                .execute()
            )
            logger.info(f"Supabase response: {response}")

            if response.data:
                logger.info(f"Account profile found: {response.data[0]}")
                return AccountProfile(**response.data[0])
            else:
                logger.error(f"No account profile found for account_id: {account_id}")
                return None
        except Exception as e:
            logger.exception(f"Error fetching account profile: {str(e)}")
            raise ValueError(f"Error fetching account profile: {str(e)}")
