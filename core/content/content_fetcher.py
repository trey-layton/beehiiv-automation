import logging
from core.content.beehiiv_content import get_beehiiv_post_id, get_beehiiv_post_content
from core.models.account_profile import AccountProfile

logger = logging.getLogger(__name__)


async def fetch_beehiiv_content(account_profile: AccountProfile, edition_url: str) -> dict:
    try:
        logger.info(
            f"Fetching Beehiiv content for user {account_profile.account_id}"
        )

        if not account_profile.beehiiv_api_key:
            raise ValueError("Missing Beehiiv API key")
        if not account_profile.publication_id:
            raise ValueError("Missing Beehiiv publication ID")

        post_id = get_beehiiv_post_id(edition_url)
        if not post_id:
            raise ValueError("Invalid Beehiiv post URL")

        post_content = get_beehiiv_post_content(account_profile, post_id)
        if not post_content:
            raise ValueError("Failed to retrieve Beehiiv post content")

        content_data = {
            "subscribe_url": account_profile.subscribe_url,
            "free_content": post_content.get("free_content"),
            "web_url": post_content.get("web_url"),
            "thumbnail_url": post_content.get("thumbnail_url"),
        }

        return content_data
    except Exception as e:
        logger.error(f"Error while fetching Beehiiv content: {str(e)}")
        raise
