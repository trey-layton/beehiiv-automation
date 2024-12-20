import asyncio
import json
import logging
from supabase import Client, create_client
from core.models.account_profile import AccountProfile
from core.content.beehiiv_handler import (
    get_beehiiv_post_content,
    fetch_beehiiv_content,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock values for testing
API_KEY = "UE6Sub549e7KUC8zMLHSsx4nbeBTaJ1lZ08g81sHyUukA7cwpFh5ISuwp8ijd8uJ"
PUBLICATION_ID = "pub_fc6b1e23-d357-41bf-ade9-83be12375558"
POST_ID = "post_e2f4d94e-9aca-4e57-9ff2-faba4aaf2653"
SUBSCRIBE_URL = "https://example.com/subscribe"

# Create mock AccountProfile
account_profile = AccountProfile(
    beehiiv_api_key=API_KEY,
    publication_id=PUBLICATION_ID,
    subscribe_url=SUBSCRIBE_URL,
    account_id="26f2ed9a-66b7-441a-b349-bf92d806c49a",
)

# Mock Supabase client
# Replace these with your actual Supabase credentials if testing with real Supabase
SUPABASE_URL = "http://127.0.0.1:54321"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def main():
    try:
        # Use the handler's fetch_beehiiv_content function instead of our custom implementation
        content_data = await fetch_beehiiv_content(
            account_profile=account_profile, post_id=POST_ID, supabase=supabase
        )

        # Print the resulting content_data
        logger.info(json.dumps(content_data, indent=2))

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
