import json
import logging
import re
from typing import Dict, Any, List, Optional
import aiohttp
from newspaper import Article
from urllib.parse import urlparse
from core.models.account_profile import AccountProfile
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


class LinkMetadataExtractor:
    PLATFORM_HANDLERS = {
        "twitter.com": "_handle_twitter",
        "x.com": "_handle_twitter",
        "linkedin.com": "_handle_linkedin",
        "finance.yahoo.com": "_handle_stock",
        "seekingalpha.com": "_handle_stock",
        "bloomberg.com": "_handle_stock",
    }

    async def get_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata, defaulting to newspaper unless URL matches known platform"""
        domain = urlparse(url).netloc.lower()

        # Check if domain matches any known platforms
        for platform_domain, handler_name in self.PLATFORM_HANDLERS.items():
            if platform_domain in domain:
                handler = getattr(self, handler_name)
                return await handler(url)

        # Default to newspaper for article extraction
        try:
            return await self._extract_article_metadata(url)
        except Exception as e:
            logger.error(f"Failed to extract article metadata: {e}")
            return await self._extract_basic_metadata(url)

    async def _extract_article_metadata(self, url: str) -> Dict[str, Any]:
        """Use newspaper for article extraction"""
        article = Article(url)
        article.download()
        article.parse()

        return {
            "url": url,
            "type": "article",
            "title": article.title,
            "description": article.meta_description,
            "image": article.top_image,
            "authors": article.authors,
            "publish_date": article.publish_date,
            "text": article.text[:300] if article.text else None,  # Preview only
        }

    async def _extract_basic_metadata(self, url: str) -> Dict[str, Any]:
        """Extract basic metadata when article parsing fails"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

                # Extract basic meta tags
                title = self._extract_meta_content(
                    html, "title"
                ) or self._extract_meta_content(html, "og:title")
                description = self._extract_meta_content(
                    html, "description"
                ) or self._extract_meta_content(html, "og:description")

                return {
                    "url": url,
                    "type": "default",
                    "title": title,
                    "description": description,
                }

    async def _handle_twitter(self, url: str) -> Dict[str, Any]:
        """Handle Twitter links"""
        return {"url": url, "type": "twitter", "platform": "twitter"}

    async def _handle_linkedin(self, url: str) -> Dict[str, Any]:
        """Handle LinkedIn links"""
        return {"url": url, "type": "linkedin", "platform": "linkedin"}

    async def _handle_stock(self, url: str) -> Dict[str, Any]:
        """Handle financial links"""
        return {"url": url, "type": "stock", "platform": "financial"}

    def _extract_meta_content(self, html: str, meta_name: str) -> Optional[str]:
        """Helper to extract content from meta tags"""
        match = re.search(
            f"<meta[^>]*(?:name|property)=['\"]{meta_name}['\"][^>]*content=['\"](.*?)['\"]",
            html,
        )
        if match:
            return match.group(1)
        return None


async def check_link_relevance(
    content_data: Dict[str, Any],
    links: List[Dict[str, str]],  # List of {url: str, text: str}
    content_type: str,
    account_profile: AccountProfile,
) -> Dict[str, Any]:
    """Evaluate link relevance for social media posts."""
    if not links:
        return content_data

    metadata_extractor = LinkMetadataExtractor()

    # Enrich links with metadata
    enriched_links = []
    for link in links:
        try:
            metadata = await metadata_extractor.get_metadata(link["url"])
            enriched_links.append({**link, **metadata})
        except Exception as e:
            logger.error(f"Failed to extract metadata for {link['url']}: {e}")
            enriched_links.append(link)

    system_message = {
        "role": "system",
        "content": """You are an AI assistant specializing in evaluating link relevance for social media posts.
        Be discerning in deciding whether a link adds value. Guidelines:
        - Links should provide meaningful additional context or value
        - Links to sources/references are generally valuable
        - Links to related content may be valuable if highly relevant
        - Only include one link per post
        - Links that are just promotional or tangential should be removed
        - Consider platform-specific metadata when available
        
        Return the content structure with at most one relevant link per post.""",
    }

    user_message = {
        "role": "user",
        "content": f"""
        Content to evaluate:
        {json.dumps(content_data, indent=2)}
        
        Available links with metadata:
        {json.dumps(enriched_links, indent=2)}
        
        Account preferences:
        {account_profile.json()}
        """,
    }

    try:
        response = await call_language_model(
            system_message, user_message, tier="medium"
        )

        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if not match:
            logger.error("No content found between delimiters in response.")
            return content_data

        extracted_content = match.group(1).strip()
        cleaned_content = re.sub(r"\s+", " ", extracted_content)
        cleaned_content = cleaned_content.encode("utf-8", "ignore").decode("utf-8")

        try:
            response_json = json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing cleaned content as JSON: {e}")
            return content_data

        if "content_container" not in response_json:
            logger.error(f"'content_container' missing in response: {response_json}")
            return content_data

        if not isinstance(response_json["content_container"], list):
            logger.error("content_container is not a list")
            return content_data

        # Validate links against original set
        for item in response_json["content_container"]:
            if "links" in item:
                valid_links = []
                for link in item["links"]:
                    if any(l["url"] == link["url"] for l in enriched_links):
                        valid_links.append(link)
                        break  # Only keep the first valid link
                if valid_links:
                    item["links"] = valid_links
                else:
                    item.pop("links", None)

        return response_json

    except Exception as e:
        logger.error(f"Error in link relevance check: {str(e)}", exc_info=True)
        return content_data
