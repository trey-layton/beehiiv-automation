import tweepy
from typing import Tuple
import logging
import time
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
    try:
        logger.info(f"Starting the main process for user {user_id}")
        logger.info(f"Database path: {db_path}")
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

        logger.info(f"Loaded user config for user {user_id}")
        logger.debug(f"User config: {user_config}")

        # Combine app-level config with user-specific config
        twitter_config = {
            "twitter_api_key": config["twitter_api_key"],
            "twitter_api_secret": config["twitter_api_secret"],
            "twitter_access_key": user_config["twitter_access_key"],
            "twitter_access_secret": user_config["twitter_access_secret"],
        }

        # Create Tweepy Client for v2 API
        client = tweepy.Client(
            consumer_key=twitter_config["twitter_api_key"],
            consumer_secret=twitter_config["twitter_api_secret"],
            access_token=twitter_config["twitter_access_key"],
            access_token_secret=twitter_config["twitter_access_secret"],
        )

        # Create Tweepy API v1.1 object for media upload (v2 doesn't support media upload yet)
        auth = tweepy.OAuthHandler(
            twitter_config["twitter_api_key"], twitter_config["twitter_api_secret"]
        )
        auth.set_access_token(
            twitter_config["twitter_access_key"],
            twitter_config["twitter_access_secret"],
        )
        api = tweepy.API(auth)

        api_key = config["anthropic_api_key"]

        # Fetch content from Beehiiv
        content_data = fetch_beehiiv_content(user_id, edition_url, user_config)
        original_content = content_data.get("free_content")

        if not original_content:
            logger.error(f"Failed to fetch content for user {user_id}")
            return False, "Failed to fetch content from Beehiiv"

        logger.info(f"Fetched content (first 500 chars): {original_content[:500]}")

        article_link = content_data.get("web_url")
        thumbnail_url = content_data.get("thumbnail_url")
        subscribe_url = user_config.get("subscribe_url")

        if not subscribe_url:
            logger.error(f"Subscribe URL not found for user {user_id}")
            return (
                False,
                "Subscribe URL not found. Please use the /register command to set your subscribe URL.",
            )

        # Prepare the follow-up tweet text
        follow_up_tweet = f"subscribe now to read it for free! {subscribe_url}"

        if generate_precta:
            precta_tweet = generate_precta_tweet(original_content, api_key)
            logger.info(f"Generated precta tweet: {precta_tweet}")
            precta_response = client.create_tweet(text=precta_tweet)
            precta_tweet_id = precta_response.data["id"]

            # Wait for 30 seconds
            time.sleep(30)

            # Post the follow-up tweet with the subscription link
            client.create_tweet(
                text=follow_up_tweet, in_reply_to_tweet_id=precta_tweet_id
            )

        if generate_postcta:
            postcta_tweet = generate_postcta_tweet(original_content, api_key)
            logger.info(f"Generated postcta tweet: {postcta_tweet}")

            try:
                # Use the existing upload_media function
                media_id = upload_media(thumbnail_url, user_id, twitter_config)

                postcta_response = client.create_tweet(
                    text=postcta_tweet, media_ids=[media_id]
                )
                postcta_tweet_id = postcta_response.data["id"]

                # Wait for 30 seconds
                time.sleep(30)

                # Post the follow-up tweet with the subscription link
                client.create_tweet(
                    text=follow_up_tweet, in_reply_to_tweet_id=postcta_tweet_id
                )
            except Exception as media_error:
                logger.error(f"Failed to upload media: {str(media_error)}")
                # If media upload failed, post the tweet without media
                postcta_response = client.create_tweet(text=postcta_tweet)
                postcta_tweet_id = postcta_response.data["id"]

                # Wait for 30 seconds
                time.sleep(30)

                # Post the follow-up tweet with the subscription link
                client.create_tweet(
                    text=follow_up_tweet, in_reply_to_tweet_id=postcta_tweet_id
                )

        if generate_thread:
            thread_tweets = generate_thread_tweets(
                original_content, article_link, api_key
            )
            logger.info(f"Generated thread tweets: {thread_tweets}")

            # Post the thread
            previous_tweet_id = None
            for tweet in thread_tweets:
                response = client.create_tweet(
                    text=tweet, in_reply_to_tweet_id=previous_tweet_id
                )
                previous_tweet_id = response.data["id"]

            # Wait for 30 seconds after the last tweet in the thread
            time.sleep(30)

            # Post the follow-up tweet with the subscription link
            client.create_tweet(
                text=follow_up_tweet, in_reply_to_tweet_id=previous_tweet_id
            )

        logger.info("Main process completed successfully")
        return True, "Process completed successfully."

    except Exception as e:
        logger.exception(f"An error occurred in run_main_process for user {user_id}:")
        return False, str(e)
