from typing import Any, Dict, Tuple
from core.content.content_fetcher import fetch_beehiiv_content
from core.social_media.threads.generate_threads import (
    generate_pre_cta_thread,
    generate_post_cta_thread,
    generate_thread_posts,
)
from core.social_media.twitter.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweets,
    generate_long_form_tweet,
)
from core.social_media.linkedin.generate_linkedin_post import generate_linkedin_post
from core.social_media.twitter.tweet_handler import TweetHandler
import logging
from core.config.user_config import load_user_config
from core.encryption.encryption import get_key, get_key_path
import os

logger = logging.getLogger(__name__)


async def run_main_process(
    user_id: str,
    edition_url: str,
    generate_precta_x: bool = False,
    generate_postcta_x: bool = False,
    generate_thread_x: bool = False,
    generate_long_form_x: bool = False,
    generate_precta_threads: bool = False,
    generate_postcta_threads: bool = False,
    generate_thread_threads: bool = False,
    generate_linkedin: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        user_config = load_user_config(user_id)
        if not user_config:
            return False, "User not found or not authenticated", {}

        logger.info(f"Fetching Beehiiv content for user {user_id}")

        beehiiv_api_key = user_config.get("beehiiv_api_key")
        if not beehiiv_api_key:
            return False, "Missing configuration key: 'beehiiv_api_key'", {}

        beehiiv_publication_id = user_config.get("publication_id")
        if not beehiiv_publication_id:
            return False, "Missing configuration key: 'publication_id'", {}

        twitter_credentials = {
            "twitter_api_key": os.getenv("TWITTER_API_KEY"),
            "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
            "twitter_access_key": user_config.get("twitter_access_key"),
            "twitter_access_secret": user_config.get("twitter_access_secret"),
        }

        tweet_handler = TweetHandler(twitter_credentials)
        tweet_handler.set_user_id(user_id)

        try:
            tweet_handler.initialize_twitter_oauth()
        except ValueError as ve:
            return False, f"Error initializing Twitter OAuth: {str(ve)}", {}

        # Fetch content data
        try:
            content_data = await fetch_beehiiv_content(user_id, edition_url)
        except Exception as e:
            return False, f"Error fetching Beehiiv content: {str(e)}", {}

        original_content = content_data.get("free_content")
        article_link = content_data.get("web_url")
        thumbnail_url = content_data.get("thumbnail_url")

        # Retrieve user-specific data
        subscribe_url = user_config.get("subscribe_url")
        example_tweet = user_config.get("example_tweet", "")

        if not original_content:
            return False, "Failed to fetch content from Beehiiv", {}

        if not subscribe_url:
            return (
                False,
                "Subscribe URL not found. Please update your profile with a subscribe URL.",
                {},
            )

        generated_content = {}

        if generate_precta_x:
            logger.info("Generating pre-CTA X post")
            precta_x = await generate_precta_tweet(
                original_content, user_config.get("openai_api_key"), example_tweet
            )
            generated_content["precta_x"] = {
                "text": precta_x,
                "reply": f"subscribe for free to get it in your inbox! {subscribe_url}",
            }

        if generate_postcta_x:
            logger.info("Generating post-CTA X post")
            postcta_x = await generate_postcta_tweet(
                original_content, user_config.get("openai_api_key"), example_tweet
            )
            generated_content["postcta_x"] = {
                "text": postcta_x,
                "reply": f"check out the full thing online now! {article_link}",
                "media_url": thumbnail_url,
            }

        if generate_thread_x:
            logger.info("Generating X thread")
            thread_x = await generate_thread_tweets(
                original_content, article_link, user_config.get("openai_api_key")
            )
            logger.debug(f"Generated thread_x: {thread_x}")  # Add this line
            generated_content["thread_x"] = thread_x

        if generate_long_form_x:
            logger.info("Generating long-form X post")
            example_tweet = user_config.get(
                "example_long_form_tweet", ""
            )  # Get the example tweet from user config
            long_form_x = await generate_long_form_tweet(
                original_content, user_config.get("openai_api_key")
            )
            generated_content["long_form_x"] = long_form_x

        if generate_linkedin:
            logger.info("Generating LinkedIn post")
            linkedin_post = await generate_linkedin_post(
                original_content,
                user_config.get("openai_api_key"),
                example_tweet,
            )
            generated_content["linkedin"] = linkedin_post
        if generate_precta_threads:
            logger.info("Generating pre-CTA Thread post")
            precta_thread = await generate_pre_cta_thread(
                original_content,
                user_config.get("openai_api_key"),
                example_tweet,  # You might want to add a separate example_thread_post to user_config
            )
            generated_content["precta_thread"] = precta_thread

        if generate_postcta_threads:
            logger.info("Generating post-CTA Thread post")
            postcta_thread = await generate_post_cta_thread(
                original_content,
                user_config.get("openai_api_key"),
                example_tweet,  # You might want to add a separate example_thread_post to user_config
            )
            generated_content["postcta_thread"] = postcta_thread

        if generate_thread_threads:
            logger.info("Generating Thread posts")
            thread_thread = await generate_thread_posts(
                original_content,
                user_config.get("openai_api_key"),
                example_tweet,  # You might want to add a separate example_thread_post to user_config
            )
            generated_content["thread_thread"] = thread_thread

        if not generated_content:
            logger.info("No content types were selected for generation")
            return True, "No content was generated as no options were selected.", {}

        logger.info("Content generation completed successfully")
        return (
            True,
            "Content generated successfully. Please review before posting.",
            generated_content,
        )
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred in run_main_process for user {user_id}:"
        )
        return False, f"An unexpected error occurred: {str(e)}", {}
