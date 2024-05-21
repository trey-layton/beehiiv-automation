import re
import http.client
import json
import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from config import get_config


logger = logging.getLogger(__name__)


def load_env_variables():
    load_dotenv(dotenv_path="/Users/treylayton/Desktop/Coding/beehiiv_project/.env")


def get_beehiiv_post_id(beehiiv_url):
    try:
        post_id_match = re.search(
            r"https://app\.beehiiv\.com/posts/([a-z0-9-]+)", beehiiv_url
        )
        return post_id_match.group(1) if post_id_match else None
    except Exception as e:
        logger.exception("Error while extracting Beehiiv post ID:")
        raise


def clean_html_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    text_elements = soup.find_all(["h1", "h2", "h3", "p", "li"])
    clean_text = "\n".join([element.get_text() for element in text_elements])
    return clean_text


def get_beehiiv_post_content(beehiiv_api_key, publication_id, post_id):
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
        data = res.read().decode("utf-8")
        json_data = json.loads(data)

        # Debug: log the entire JSON response
        print("Beehiiv API response:", json.dumps(json_data, indent=4))

        if "data" in json_data:
            data = json_data["data"]
            post_content = (
                clean_html_content(data["content"]["free"]["web"])
                if "content" in data
                and "free" in data["content"]
                and "web" in data["content"]["free"]
                else None
            )
            web_url = data["web_url"] if "web_url" in data else None
            thumbnail_url = data["thumbnail_url"] if "thumbnail_url" in data else None

            return {
                "post_id": post_id,
                "free_content": post_content,
                "web_url": web_url,
                "thumbnail_url": thumbnail_url,
            }
        else:
            logger.error("Invalid response structure: 'data' key not found")
            return None
    except Exception as e:
        logger.exception("Error while fetching Beehiiv post content:")
        raise


# The script's final result is a dictionary containing the post ID, free content, web URL, and thumbnail URL of a specified Beehiiv post. This dictionary can then be used in subsequent steps of your process to generate social media posts and relevant links.
