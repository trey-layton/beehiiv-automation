import re
import http.client
import json
import logging
from typing import Optional, Dict, Any
from content.html_utils import clean_html_content

logger = logging.getLogger(__name__)


def get_beehiiv_post_id(beehiiv_url: str) -> Optional[str]:
    """
    Extracts the post ID from a given Beehiiv URL.

    Args:
        beehiiv_url (str): The URL of the Beehiiv post.

    Returns:
        Optional[str]: The extracted post ID or None if extraction fails.
    """
    try:
        post_id_match = re.search(
            r"https://app\.beehiiv\.com/posts/([a-z0-9-]+)", beehiiv_url
        )
        return post_id_match.group(1) if post_id_match else None
    except Exception as e:
        logger.exception("Error while extracting Beehiiv post ID:")
        raise


def get_beehiiv_post_content(
    user_id: str, post_id: str, config: dict
) -> Optional[Dict[str, Any]]:
    """
    Retrieves and returns content for a specific Beehiiv post.

    Args:
        user_id (str): The user ID requesting the content.
        post_id (str): The post ID to retrieve content for.
        config (dict): The configuration dictionary.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing post details like post_id, free_content, web_url, and thumbnail_url,
                                  or None if the content could not be retrieved.
    """
    try:
        beehiiv_api_key = config["beehiiv_api_key"]
        publication_id = config["publication_id"]
    except KeyError as e:
        logger.error("Missing configuration key: %s", e)
        return None

    try:
        conn = http.client.HTTPSConnection("api.beehiiv.com")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {beehiiv_api_key}",
        }
        conn.request(
            "GET",
            f"/v2/publications/pub_{publication_id}/posts/post_{post_id}?expand%5B%5D=free_web_content",
            headers=headers,
        )

        res = conn.getresponse()
        if res.status != 200:
            logger.error("Failed to fetch Beehiiv post content: HTTP %s", res.status)
            return None

        data = res.read().decode("utf-8")
        json_data = json.loads(data)

        # Debug: log the entire JSON response
        # logger.debug("Beehiiv API response: %s", json.dumps(json_data, indent=4))

        if "data" in json_data:
            data = json_data["data"]
            post_content = (
                clean_html_content(data["content"]["free"]["web"])
                if "content" in data
                and "free" in data["content"]
                and "web" in data["content"]["free"]
                else None
            )
            web_url = data.get("web_url")
            thumbnail_url = data.get("thumbnail_url")

            return {
                "post_id": post_id,
                "free_content": post_content,
                "web_url": web_url,
                "thumbnail_url": thumbnail_url,
            }
        else:
            logger.error("Invalid response structure: 'data' key not found")
            return None
    except http.client.HTTPException as e:
        logger.exception("HTTP error while fetching Beehiiv post content:")
        return None
    except json.JSONDecodeError as e:
        logger.exception("Error decoding JSON response:")
        return None
    except Exception as e:
        logger.exception("Error while fetching Beehiiv post content:")
        raise
