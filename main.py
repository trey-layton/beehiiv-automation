import logging
import argparse
from config.environment import load_environment, get_config
from config.user_config import load_user_config
from encryption.encryption import load_key
from social_media.twitter.tweet_posting import (
    post_pre_tweet,
    post_post_tweet,
    post_thread,
)
from social_media.twitter.media_upload import upload_media
from content.content_fetcher import fetch_beehiiv_content
from content.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweets,
)
from discord_functionality.discord_bot import run_discord_bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(
    user_id: str,
    edition_url: str,
    generate_precta: bool,
    generate_postcta: bool,
    generate_thread: bool,
) -> None:
    try:
        logger.info("Starting the main function")
        load_environment()
        config = get_config()

        key_path = "secret.key"
        user_config_path = "user_config.enc"
        key = load_key(key_path)
        user_config = load_user_config(user_config_path, key, user_id)
        if user_config is None:
            raise ValueError("User configuration is missing or invalid")

        twitter_credentials = {
            "twitter_api_key": config["twitter_api_key"],
            "twitter_api_secret": config["twitter_api_secret"],
            "twitter_access_key": user_config["twitter_access_key"],
            "twitter_access_secret": user_config["twitter_access_secret"],
        }

        content_data = fetch_beehiiv_content(user_id, edition_url, user_config)
        original_content = content_data["free_content"]
        article_link = content_data["web_url"]
        thumbnail_url = content_data["thumbnail_url"]
        subscribe_url = content_data["subscribe_url"]

        api_key = config["openai_api_key"]

        if generate_precta:
            precta_tweet = generate_precta_tweet(original_content, api_key)
            logger.info(f"Generated precta tweet: {precta_tweet}")
            post_pre_tweet(precta_tweet, subscribe_url, twitter_credentials)

        if generate_postcta:
            postcta_tweet = generate_postcta_tweet(original_content, api_key)
            logger.info(f"Generated postcta tweet: {postcta_tweet}")
            media_id = upload_media(thumbnail_url, user_id, twitter_credentials)
            logger.info(f"Uploaded media with ID: {media_id}")
            post_post_tweet(postcta_tweet, article_link, media_id, twitter_credentials)

        if generate_thread:
            thread_tweets = generate_thread_tweets(
                original_content, article_link, api_key
            )
            logger.info(f"Generated thread tweets: {thread_tweets}")
            post_thread(thread_tweets, twitter_credentials)

        # Start Discord bot with configurations and encryption key
        run_discord_bot(config, key)

        logger.info("Main function completed successfully")
    except Exception as e:
        logger.exception("An error occurred:")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate and post tweets from Beehiiv content."
    )
    parser.add_argument("user_id", help="User ID for fetching Beehiiv content")
    parser.add_argument(
        "edition_url", help="URL of the specific edition to fetch content for"
    )
    parser.add_argument(
        "--precta",
        action="store_true",
        help="Generate and post pre-newsletter CTA tweet",
    )
    parser.add_argument(
        "--postcta",
        action="store_true",
        help="Generate and post post-newsletter CTA tweet",
    )
    parser.add_argument(
        "--thread", action="store_true", help="Generate and post thread tweets"
    )
    args = parser.parse_args()

    main(args.user_id, args.edition_url, args.precta, args.postcta, args.thread)
