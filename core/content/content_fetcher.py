import logging
from core.content.beehiiv_content import get_beehiiv_post_id, get_beehiiv_post_content
from core.auth.stack_auth_client import stackAuthClient
from core.config.user_config import load_user_config
from core.encryption.encryption import get_key
import os

logger = logging.getLogger(__name__)


async def fetch_beehiiv_content(user_id: str, edition_url: str) -> dict:
    try:
        logger.info(f"Fetching Beehiiv content for user {user_id}")

        user_data = load_user_config(user_id)
        if not user_data:
            raise ValueError(f"Failed to get user data for user {user_id}")

        beehiiv_api_key = user_data.get("beehiiv_api_key")
        if not beehiiv_api_key:
            raise ValueError("Missing configuration key: 'beehiiv_api_key'")

        beehiiv_publication_id = user_data.get("publication_id")
        if not beehiiv_publication_id:
            raise ValueError("Missing configuration key: 'publication_id'")

        post_id = get_beehiiv_post_id(edition_url)
        if not post_id:
            raise ValueError("Invalid Beehiiv post URL")

        post_content = get_beehiiv_post_content(
            user_id,
            post_id,
            {
                "beehiiv_api_key": beehiiv_api_key,
                "beehiiv_publication_id": beehiiv_publication_id,
            },
        )
        if not post_content:
            raise ValueError("Failed to retrieve Beehiiv post content")

        logger.info(f"Post content: {post_content}")

        content_data = {
            "subscribe_url": user_data.get("subscribe_url"),
            "free_content": post_content.get("free_content"),
            "raw_content": post_content.get("raw_content"),
            "web_url": post_content.get("web_url"),
            "thumbnail_url": post_content.get("thumbnail_url"),
        }

        logger.info(f"Content data: {content_data}")
        logger.info(f"Successfully fetched Beehiiv content for user {user_id}")
        return content_data
    except Exception as e:
        logger.exception(f"Error while fetching Beehiiv content: {str(e)}")
        raise
