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

logger = logging.getLogger(__name__)


async def run_main_process(
    user_profile: Dict[str, Any],
    edition_url: str,
    generate_precta_tweet: bool = False,
    generate_postcta_tweet: bool = False,
    generate_thread_tweet: bool = False,
    generate_long_form_tweet: bool = False,
    generate_linkedin: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    logger.info(f"run_main_process started for user {user_profile['id']}")
    try:
        if not user_profile:
            return False, "User profile not found. Please update your profile.", {}

        if not user_profile.get("beehiiv_api_key") or not user_profile.get(
            "publication_id"
        ):
            logger.warning(f"Beehiiv credentials missing for user {user_profile['id']}")
            return (
                False,
                "Beehiiv credentials are missing. Please connect your Beehiiv account.",
                {},
            )

        logger.info(f"Fetching Beehiiv content for URL: {edition_url}")
        content_data = await fetch_beehiiv_content(user_profile, edition_url)
        original_content = content_data.get("free_content")

        if not original_content:
            logger.error("Failed to fetch content from Beehiiv")
            return False, "Failed to fetch content from Beehiiv", {}

        logger.info("Content fetched successfully, generating requested content types")
        generated_content = {}

        if generate_precta_tweet:
            generated_content["precta_tweet"] = await generate_precta_tweet(
                original_content, user_profile
            )

        if generate_postcta_tweet:
            generated_content["postcta_tweet"] = await generate_postcta_tweet(
                original_content, user_profile
            )

        if generate_thread_tweet:
            generated_content["thread_tweet"] = await generate_thread_tweet(
                original_content, content_data.get("web_url"), user_profile
            )

        if generate_long_form_tweet:
            generated_content["long_form_tweet"] = await generate_long_form_tweet(
                original_content, user_profile
            )

        if generate_linkedin:
            generated_content["linkedin"] = await generate_linkedin_post(
                original_content, user_profile
            )

        logger.info("Content generation completed successfully")
        return True, "Content generated successfully", generated_content

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
