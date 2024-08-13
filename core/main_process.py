import logging
from typing import Any, Dict, Tuple
from core.content.content_fetcher import fetch_beehiiv_content
import json
from core.models.account_profile import AccountProfile

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    post_id: str,
    content_type
) -> Tuple[bool, str, Dict[str, Any]]:
    logger.info(f"run_main_process started for user {account_profile.account_id}")
    try:
        logger.info(f"Fetching Beehiiv content for Post: {post_id}")
        content_data = await fetch_beehiiv_content(account_profile, post_id)
        original_content = content_data.get("free_content")

        if not original_content:
            logger.error("Failed to fetch content from Beehiiv")
            return False, "Failed to fetch content from Beehiiv", {}

        logger.info("Content fetched successfully, generating requested content types")
        generated_content = {}

        if content_type == "precta_tweet":
            from core.social_media.twitter.generate_tweets import generate_precta_tweet
            precta_tweet = await generate_precta_tweet(original_content, account_profile)
            generated_content = {
                "provider": "twitter",
                "type": "precta_tweet",
                "content": [
                    {
                        "type": "post",
                        "text": precta_tweet
                    }
                ]
            }

        elif content_type == "postcta_tweet":
            from core.social_media.twitter.generate_tweets import generate_postcta_tweet
            postcta_tweet = await generate_postcta_tweet(original_content, account_profile)
            generated_content = {
                "provider": "twitter",
                "type": "postcta_tweet",
                "content": [
                    {
                        "type": "post",
                        "text": postcta_tweet
                    }
                ]
            }

        elif content_type == "thread_tweet":
            from core.social_media.twitter.generate_tweets import generate_thread_tweet
            thread_tweet = await generate_thread_tweet(original_content, content_data.get("web_url"), account_profile)
            generated_content = {
                "provider": "twitter",
                "type": "thread_tweet",
                "content": thread_tweet
            }

        elif content_type == "long_form_tweet":
            from core.social_media.twitter.generate_tweets import (
                generate_long_form_tweet,
            )

            long_form_tweet = await generate_long_form_tweet(
                original_content, account_profile
            )
            generated_content = {
                "provider": "twitter",
                "type": "long_form_tweet",
                "content": [
                    {
                        "type": "long_post",
                        "text": long_form_tweet
                    }
                ]
            }

        elif content_type == "linkedin":
            from core.social_media.linkedin.generate_linkedin_post import (
                generate_linkedin_post,
            )
            linkedin = await generate_linkedin_post(
                original_content, account_profile
            )
            generated_content = {
                "provider": "linkedin",
                "type": "linkedin",
                "content": [
                    {
                        "type": "post",
                        "text": linkedin
                    }
                ]
            }

        logger.info("Content generation completed successfully")
        return True, "Content generated successfully", generated_content

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
