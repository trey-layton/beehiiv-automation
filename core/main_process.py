import logging
from typing import Any, Dict, Tuple
from core.content.content_fetcher import fetch_beehiiv_content
from core.social_media.twitter.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweet,
    generate_long_form_tweet,
)
from core.social_media.linkedin.generate_linkedin_post import generate_linkedin_post
from core.config.user_config import load_user_config

logger = logging.getLogger(__name__)


async def run_main_process(
    user_config: Dict[str, Any],
    edition_url: str,
    precta_tweet: bool = False,
    postcta_tweet: bool = False,
    thread_tweet: bool = False,
    long_form_tweet: bool = False,
    linkedin: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    logger.info(f"run_main_process started for user {user_config['account_id']}")
    try:
        if not user_config:
            return False, "User profile not found. Please update your profile.", {}

        if not user_config.get("beehiiv_api_key") or not user_config.get(
            "publication_id"
        ):
            logger.warning(f"Beehiiv credentials missing for user {user_config['account_id']}")
            return (
                False,
                "Beehiiv credentials are missing. Please connect your Beehiiv account.",
                {},
            )

        logger.info(f"Fetching Beehiiv content for URL: {edition_url}")
        content_data = await fetch_beehiiv_content(user_config, edition_url)
        original_content = content_data.get("free_content")

        if not original_content:
            logger.error("Failed to fetch content from Beehiiv")
            return False, "Failed to fetch content from Beehiiv", {}

        logger.info("Content fetched successfully, generating requested content types")
        generated_content = {}

        if precta_tweet:
            generated_content["precta_tweet"] = await generate_precta_tweet(
                original_content, user_config
            )

        if postcta_tweet:
            generated_content["postcta_tweet"] = await generate_postcta_tweet(
                original_content, user_config
            )

        if thread_tweet:
            generated_content["thread_tweet"] = await generate_thread_tweet(
                original_content, content_data.get("web_url"), user_config
            )

        if long_form_tweet:
            generated_content["long_form_tweet"] = await generate_long_form_tweet(
                original_content, user_config
            )

        if linkedin:
            generated_content["linkedin"] = await generate_linkedin_post(
                original_content, user_config
            )

        logger.info("Content generation completed successfully")
        return True, "Content generated successfully", generated_content

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
