import logging
from typing import Tuple
from core.config.environment import load_environment, get_config
from core.config.user_config import load_user_config
from core.encryption.encryption import load_key
from core.content.content_fetcher import fetch_beehiiv_content
from core.content.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweets,
)
from core.social_media.twitter.media_upload import upload_media
from core.social_media.twitter.tweet_handler import TweetHandler

logger = logging.getLogger(__name__)


def run_main_process(
    user_id: str,
    edition_url: str,
    generate_precta: bool,
    generate_postcta: bool,
    generate_thread: bool,
    key_path: str,
    db_path: str,
) -> Tuple[bool, str]:
    logger.debug(
        f"Starting main process for user {user_id}, edition URL: {edition_url}"
    )
    try:
        load_environment()
        config = get_config()
        key = load_key(key_path)
        user_config = load_user_config(key, user_id)

        if user_config is None:
            logger.error(f"User configuration not found for user {user_id}")
            return (
                False,
                "User configuration not found. Please use the /register command first.",
            )

        twitter_config = {
            "twitter_api_key": config["twitter_api_key"],
            "twitter_api_secret": config["twitter_api_secret"],
            "twitter_access_key": user_config["twitter_access_key"],
            "twitter_access_secret": user_config["twitter_access_secret"],
        }

        tweet_handler = TweetHandler(twitter_config)
        api_key = config["anthropic_api_key"]

        content_data = fetch_beehiiv_content(user_id, edition_url, user_config)
        original_content = content_data.get("free_content")
        article_link = content_data.get("web_url")
        thumbnail_url = content_data.get("thumbnail_url")
        subscribe_url = user_config.get("subscribe_url")

        if not original_content:
            logger.error(f"Failed to fetch content for user {user_id}")
            return False, "Failed to fetch content from Beehiiv"

        if not subscribe_url:
            logger.error(f"Subscribe URL not found for user {user_id}")
            return (
                False,
                "Subscribe URL not found. Please use the /register command to set your subscribe URL.",
            )

        if generate_precta:
            logger.info("Generating pre-CTA tweet")
            precta_tweet = generate_precta_tweet(original_content, api_key)
            tweet_handler.post_pre_cta_tweet(precta_tweet, subscribe_url)

        if generate_postcta:
            logger.info("Generating post-CTA tweet")
            postcta_tweet = generate_postcta_tweet(original_content, api_key)
            media_id = upload_media(thumbnail_url, user_id, twitter_config)
            tweet_handler.post_post_cta_tweet(postcta_tweet, article_link, media_id)

        if generate_thread:
            logger.info(
                f"Calling generate_thread_tweets with content length: {len(original_content)}"
            )
            thread_tweets = generate_thread_tweets(
                original_content, article_link, api_key
            )
            logger.info(f"Generated {len(thread_tweets)} tweets for the thread")
            tweet_handler.post_thread(thread_tweets, article_link)

        logger.info("Tweet generation and posting completed successfully")
        return True, "Process completed successfully."

    except Exception as e:
        logger.exception(f"An error occurred in run_main_process for user {user_id}:")
        return False, str(e)
