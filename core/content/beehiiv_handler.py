import http.client
import json
import logging
import re
import uuid
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup, Comment
from supabase import Client

from core.models.account_profile import AccountProfile

logger = logging.getLogger(__name__)

# Define a whitelist of allowed tags for a cleaner, leaner HTML
# We keep basic formatting, headings, paragraphs, lists, images, and links.
ALLOWED_TAGS = {
    "a",
    "b",
    "i",
    "u",
    "em",
    "strong",
    "img",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
}


def clean_html_content(html_content: str) -> str:
    """
    This function aggressively cleans the HTML to reduce token usage while preserving:
    - Basic semantic structure: headers (h1-h6), paragraphs, lists (ul, ol, li)
    - Links (a), images (img)
    - Bold/italic formatting (b, i, em, strong)
    It:
    - Removes script, style, meta, title, head, and comments.
    - Removes all attributes except 'href' for <a>, 'src' and 'alt' for <img>.
    - Removes non-whitelisted tags but keeps their content.
    - Normalizes whitespace and removes zero-width spaces and other invisible unicode chars.
    - Removes doctype and any superfluous tags (html, body, div, table, etc.), flattening the structure.
    """

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script, style, meta, title, head, comments
    for tag in soup(["script", "style", "meta", "title", "head"]):
        tag.decompose()

    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove doctype if present
    if (
        soup.contents
        and soup.contents[0].name is None
        and "DOCTYPE" in str(soup.contents[0])
    ):
        soup.contents[0].extract()

    # Strip non-whitelisted tags, but keep their children
    for tag in soup.find_all():
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()

    # Clean attributes: only allow href on a, src/alt on img
    for tag in soup.find_all(True):
        allowed_attrs = {}
        if tag.name == "a" and tag.has_attr("href"):
            allowed_attrs["href"] = tag["href"]
        if tag.name == "img":
            if tag.has_attr("src"):
                allowed_attrs["src"] = tag["src"]
            if tag.has_attr("alt"):
                allowed_attrs["alt"] = tag["alt"]
        tag.attrs = allowed_attrs

    # Get the HTML as a string
    cleaned = str(soup)

    # Remove zero-width spaces and excessive unicode whitespace
    cleaned = cleaned.replace("\u200c", "").replace("\u00a0", " ")
    # Normalize multiple spaces/newlines
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def transform_images_into_placeholders(html_str: str) -> str:
    """
    Convert <img> tags into placeholders like [image:<URL> alt="ALT"] to preserve them through LLM steps.
    """
    soup = BeautifulSoup(html_str, "html.parser")

    for img_tag in soup.find_all("img"):
        src = img_tag.get("src", "")
        alt = img_tag.get("alt", "")
        placeholder = f'[image:{src} alt="{alt}"]'
        img_tag.replace_with(placeholder)

    return str(soup)


def transform_links_into_placeholders(html_str: str) -> str:
    """Convert <a> tags into placeholders like [link:<URL>]text[/link] to preserve through LLM steps."""
    soup = BeautifulSoup(html_str, "html.parser")

    for link_tag in soup.find_all("a"):
        href = link_tag.get("href", "")
        text = link_tag.get_text()
        placeholder = f"[link:{href}]{text}[/link]"
        link_tag.replace_with(placeholder)

    return str(soup)


def get_beehiiv_post_content(
    account_profile: AccountProfile, post_id: str
) -> Optional[Dict[str, Any]]:
    try:
        if not account_profile.beehiiv_api_key:
            raise ValueError("Missing configuration key: 'beehiiv_api_key'")
        if not account_profile.publication_id:
            raise ValueError("Missing configuration key: 'publication_id'")

        conn = http.client.HTTPSConnection("api.beehiiv.com")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {account_profile.beehiiv_api_key}",
        }

        params = urlencode({"expand[]": "free_email_content"})
        url = f"/v2/publications/{account_profile.publication_id}/posts/{post_id}?{params}"
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        data = res.read()

        if res.status != 200:
            logger.error(f"Failed to fetch Beehiiv post content: HTTP {res.status}")
            logger.error(f"Response body: {data.decode('utf-8')}")
            return None

        json_data = json.loads(data.decode("utf-8"))
        logger.debug(f"Beehiiv API response: {json.dumps(json_data, indent=4)}")

        if "data" not in json_data:
            logger.error("Invalid response structure: 'data' key not found")
            return None

        data = json_data["data"]
        content = data.get("content", {})
        free_content = content.get("free", {}).get("email")
        thumbnail_url = data.get("thumbnail_url")

        if free_content:
            free_content = clean_html_content(free_content)
            free_content = transform_images_into_placeholders(free_content)
            free_content = transform_links_into_placeholders(free_content)
        else:
            logger.warning(f"No free content found for post {post_id}")

        web_url = data.get("web_url")

        return {
            "post_id": post_id,
            "free_content": free_content,
            "web_url": web_url,
            "thumbnail_url": thumbnail_url,
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error while fetching Beehiiv post content: {str(e)}")
        raise


def extract_text(html_str: str) -> str:
    """
    If you need a purely text-based extraction, use this.
    Note: This will remove images, links, and formatting, leaving only text.
    """
    if not html_str:
        logger.error("Empty or None HTML string provided")
        raise ValueError("HTML string cannot be empty or None")

    try:
        logger.info(f"Original HTML content: {html_str[:500]}...")
        soup = BeautifulSoup(html_str, "html.parser")

        # Extract text content
        text = soup.get_text(separator="\n")
        # Clean up text
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        logger.info(f"Cleaned text: {text[:500]}...")
        return text

    except Exception as e:
        logger.exception("Error while extracting text from HTML:")
        raise


async def fetch_beehiiv_content(
    account_profile: AccountProfile, post_id: str, supabase: Client
) -> dict:
    try:
        post_content = get_beehiiv_post_content(account_profile, post_id)
        thumbnail_url = post_content.get("thumbnail_url") if post_content else None
        supabase_thumbnail_url = None

        if thumbnail_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumbnail_url) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            file_name = f"{uuid.uuid4()}.jpg"

                            # Upload to Supabase storage
                            upload_result = supabase.storage.from_("thumbnails").upload(
                                file_name, content
                            )

                            if upload_result and not isinstance(upload_result, dict):
                                public_url_result = supabase.storage.from_(
                                    "thumbnails"
                                ).get_public_url(file_name)
                                supabase_thumbnail_url = public_url_result
                            else:
                                logger.error(
                                    f"Error uploading thumbnail: {upload_result}"
                                )
            except Exception as e:
                logger.error(f"Error processing thumbnail: {str(e)}")

        content_data = {
            "subscribe_url": account_profile.subscribe_url,
            "free_content": post_content.get("free_content") if post_content else None,
            "web_url": post_content.get("web_url") if post_content else None,
            "thumbnail_url": supabase_thumbnail_url or thumbnail_url,
        }

        return content_data
    except Exception as e:
        logger.error(f"Error while fetching Beehiiv content: {str(e)}")
        raise
