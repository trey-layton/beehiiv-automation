from supabase import create_client, Client
import os
import logging

logger = logging.getLogger(__name__)

supabase: Client = create_client(
    supabase_url=os.getenv("SUPABASE_URL"), supabase_key=os.getenv("SUPABASE_KEY")
)


def load_user_config(account_id: str) -> dict:
    try:
        response = (
            supabase.table("account_profiles").select("*").eq("account_id", account_id).execute()
        )
        if response.data:
            return response.data[0]
        else:
            logger.warning(f"No user profile found for user {account_id}")
            return {}
    except Exception as e:
        logger.error(f"Error loading user config for user {account_id}: {str(e)}")
        return {}


def save_user_config(account_id: str, config: dict) -> bool:
    try:
        supabase.table("account_profiles").upsert({"account_id": account_id, **config}).execute()
        return True
    except Exception as e:
        logger.error(f"Error saving user config: {str(e)}")
        return False
