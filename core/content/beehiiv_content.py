import re
import http.client
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_html_content(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text
    text = soup.get_text()

    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())

    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # Drop blank lines
    text = "\n".join(chunk for chunk in chunks if chunk)

    return text


def get_beehiiv_post_id(beehiiv_url: str) -> Optional[str]:
    """
    Extracts the post ID from a given Beehiiv URL.

    Args:
        beehiiv_url (str): The URL of the Beehiiv post.

    Returns:
        Optional[str]: The extracted post ID (with 'post_' prefix) or None if extraction fails.
    """
    try:
        post_id_match = re.search(
            r"https://app\.beehiiv\.com/posts/([a-z0-9-]+)", beehiiv_url
        )
        if post_id_match:
            post_id = post_id_match.group(1)
            return f"post_{post_id}" if not post_id.startswith("post_") else post_id
        return None
    except Exception as e:
        logger.exception("Error while extracting Beehiiv post ID:")
        raise


def get_beehiiv_post_content(
    user_id: str, post_id: str, config: dict
) -> Optional[Dict[str, Any]]:
    try:
        beehiiv_api_key = config.get("beehiiv_api_key")
        publication_id = config.get("beehiiv_publication_id")

        if not beehiiv_api_key:
            raise ValueError("Missing configuration key: 'beehiiv_api_key'")
        if not publication_id:
            raise ValueError("Missing configuration key: 'beehiiv_publication_id'")

        conn = http.client.HTTPSConnection("api.beehiiv.com")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {beehiiv_api_key}",
        }

        params = urlencode({"expand[]": "free_web_content"})
        url = f"/v2/publications/{publication_id}/posts/{post_id}?{params}"

        logger.info(f"Sending request to Beehiiv API: URL={url}, Headers={headers}")

        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        data = res.read()

        if res.status != 200:
            logger.error(f"Failed to fetch Beehiiv post content: HTTP {res.status}")
            logger.error(f"Response body: {data.decode('utf-8')}")
            return None

        json_data = json.loads(data.decode("utf-8"))
        logger.debug(f"Beehiiv API response: {json.dumps(json_data, indent=4)}")

        if "data" in json_data:
            data = json_data["data"]
            content = data.get("content", {})
            free_content = content.get("free", {}).get("web")
            raw_content = content.get("free", {}).get("web")

            if not free_content:
                logger.warning(f"No free content found for post {post_id}")
            else:
                free_content = clean_html_content(free_content)

            web_url = data.get("web_url")
            thumbnail_url = data.get("thumbnail_url")

            result = {
                "post_id": post_id,
                "free_content": free_content,
                "raw_content": raw_content,
                "web_url": web_url,
                "thumbnail_url": thumbnail_url,
            }
            logger.info(f"Extracted post content: {result}")
            return result
        else:
            logger.error("Invalid response structure: 'data' key not found")
            return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error while fetching Beehiiv post content: {str(e)}")
        raise
