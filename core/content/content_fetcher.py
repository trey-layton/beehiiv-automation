import logging
from core.content.beehiiv_content import get_beehiiv_post_id, get_beehiiv_post_content

logger = logging.getLogger(__name__)


def fetch_beehiiv_content(user_id: str, edition_url: str, user_config: dict) -> dict:
    try:
        logger.info(f"Fetching Beehiiv content for user {user_id}")
        logger.info(f"User config: {user_config}")

        beehiiv_api_key = user_config.get("beehiiv_api_key")
        if not beehiiv_api_key:
            raise ValueError("Missing configuration key: 'beehiiv_api_key'")

        beehiiv_publication_id = user_config.get("beehiiv_publication_id")
        if not beehiiv_publication_id:
            raise ValueError("Missing configuration key: 'beehiiv_publication_id'")

        post_id = get_beehiiv_post_id(edition_url)
        if not post_id:
            raise ValueError("Invalid Beehiiv post URL")

        post_content = get_beehiiv_post_content(user_id, post_id, user_config)
        if not post_content:
            raise ValueError("Failed to retrieve Beehiiv post content")

        logger.info(f"Post content: {post_content}")  # Add this line

        content_data = {
            "subscribe_url": user_config.get("subscribe_url"),
            "free_content": post_content.get("free_content"),
            "web_url": post_content.get("web_url"),
            "thumbnail_url": post_content.get("thumbnail_url"),
        }

        logger.info(f"Content data: {content_data}")  # Add this line
        logger.info(f"Successfully fetched Beehiiv content for user {user_id}")
        return content_data
    except Exception as e:
        logger.exception(f"Error while fetching Beehiiv content: {str(e)}")
        raise
