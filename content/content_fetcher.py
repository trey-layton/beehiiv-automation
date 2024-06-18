import logging
from content.beehiiv_content import get_beehiiv_post_id, get_beehiiv_post_content

logger = logging.getLogger(__name__)


def fetch_beehiiv_content(user_id: str, edition_url: str, user_config: dict) -> dict:
    """
    Fetches content from Beehiiv for a given user and edition URL.

    Args:
        user_id (str): The user ID.
        edition_url (str): The URL of the edition to fetch content for.
        user_config (dict): The user configuration.

    Returns:
        dict: The content data including subscribe_url, free_content, web_url, and thumbnail_url.
    """
    try:
        beehiiv_api_key = user_config.get("beehiiv_api_key")
        if not beehiiv_api_key:
            raise ValueError("Missing configuration key: 'beehiiv_api_key'")

        post_id = get_beehiiv_post_id(edition_url)
        if not post_id:
            raise ValueError("Invalid Beehiiv post URL")

        # Ensure the config parameter is passed to get_beehiiv_post_content
        post_content = get_beehiiv_post_content(user_id, post_id, user_config)
        if not post_content:
            raise ValueError("Failed to retrieve Beehiiv post content")

        content_data = {
            "subscribe_url": user_config.get("subscribe_url"),
            "free_content": post_content.get("free_content"),
            "web_url": post_content.get("web_url"),
            "thumbnail_url": post_content.get("thumbnail_url"),
        }

        return content_data
    except Exception as e:
        logger.exception("Error while fetching Beehiiv content:")
        raise
