import re
import http.client
import json
from config import get_config
import logging

logger = logging.getLogger(__name__)


def get_beehiiv_post_id(beehiiv_url):
    try:
        post_id_match = re.search(
            r"https://app\.beehiiv\.com/posts/([a-z0-9-]+)", beehiiv_url
        )
        if post_id_match:
            return post_id_match.group(1)
        return None
    except Exception as e:
        logger.exception("Error while extracting Beehiiv post ID:")
        raise


def get_beehiiv_post_content(beehiiv_api_key, publication_id, post_id):
    try:
        conn = http.client.HTTPSConnection("api.beehiiv.com")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {beehiiv_api_key}",
        }
        conn.request(
            "GET",
            f"/v2/publications/{publication_id}/posts/post_{post_id}?expand%5B%5D=free_rss_content",
            headers=headers,
        )
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        json_data = json.loads(data)

        html_str = json_data["data"]["content"]["free"]["rss"]
        return html_str
    except Exception as e:
        logger.exception("Error while fetching Beehiiv post content:")
        raise
