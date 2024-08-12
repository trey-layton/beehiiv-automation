import logging
from typing import Any, Dict, Tuple
from core.content.content_fetcher import fetch_beehiiv_content
import json
from core.models.account_profile import AccountProfile

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    edition_url: str,
    generate_precta_tweet: bool = False,
    generate_postcta_tweet: bool = False,
    generate_thread_tweet: bool = False,
    generate_long_form_tweet: bool = False,
    generate_linkedin: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    logger.info(f"run_main_process started for user {account_profile.account_id}")
    try:
        logger.info(f"Fetching Beehiiv content for URL: {edition_url}")
        content_data = await fetch_beehiiv_content(account_profile, edition_url)
        original_content = content_data.get("free_content")

        if not original_content:
            logger.error("Failed to fetch content from Beehiiv")
            return False, "Failed to fetch content from Beehiiv", {}

        logger.info("Content fetched successfully, generating requested content types")
        generated_content = {}

        if generate_precta_tweet:
            from core.social_media.twitter.generate_tweets import generate_precta_tweet

            generated_content["precta_tweet"] = await generate_precta_tweet(
                original_content, account_profile
            )

        if generate_postcta_tweet:
            from core.social_media.twitter.generate_tweets import generate_postcta_tweet

            generated_content["postcta_tweet"] = await generate_postcta_tweet(
                original_content, account_profile
            )

        if generate_thread_tweet:
            from core.social_media.twitter.generate_tweets import generate_thread_tweet

            generated_content["thread_tweet"] = await generate_thread_tweet(
                original_content, content_data.get("web_url"), account_profile
            )

        if generate_long_form_tweet:
            from core.social_media.twitter.generate_tweets import (
                generate_long_form_tweet,
            )

            generated_content["long_form_tweet"] = await generate_long_form_tweet(
                original_content, account_profile
            )

        if generate_linkedin:
            from core.social_media.linkedin.generate_linkedin_post import (
                generate_linkedin_post,
            )

            generated_content["linkedin"] = await generate_linkedin_post(
                original_content, account_profile
            )

        logger.info("Content generation completed successfully")
        return True, "Content generated successfully", generated_content

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
