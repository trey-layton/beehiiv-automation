import logging
import json
import os
import argparse
from dotenv import load_dotenv
from beehiiv import get_beehiiv_post_id, get_beehiiv_post_content
from content_generation import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweets,
)
from twitter import post_tweet, upload_media
from cryptography.fernet import Fernet
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(dotenv_path="/Users/treylayton/Desktop/Coding/beehiiv_project/.env")


# Function to load the encryption key
def load_key():
    return open("secret.key", "rb").read()


# Function to decrypt data
def decrypt_data(encrypted_data, key):
    cipher_suite = Fernet(key)
    encrypted_data = base64.b64decode(encrypted_data)  # Decode base64 to bytes
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())


# Function to load user configuration
def load_user_config(user_id):
    key = load_key()
    user_config_path = "user_config.enc"

    if not os.path.exists(user_config_path):
        logger.error("user_config.enc file not found")
        return {}

    with open(user_config_path, "rb") as file:
        encrypted_data = json.loads(file.read().decode())
        encrypted_user_config = encrypted_data.get(user_id)

        if not encrypted_user_config:
            logger.error(f"No configuration found for user {user_id}")
            return {}

        return decrypt_data(encrypted_user_config.encode(), key)


# Function to fetch Beehiiv content
def fetch_beehiiv_content(user_id, edition_url):
    try:
        user_config = load_user_config(user_id)

        beehiiv_api_key = user_config["beehiiv_api_key"]
        subscribe_url = user_config["subscribe_url"]
        publication_id = user_config["publication_id"]

        post_id = get_beehiiv_post_id(edition_url)
        content_data = get_beehiiv_post_content(
            beehiiv_api_key, publication_id, post_id
        )
        content_data["subscribe_url"] = subscribe_url

        return content_data
    except Exception as e:
        logger.exception("Error while fetching Beehiiv content:")
        raise


# Function to post pre-newsletter tweet
def post_pre_tweet(precta_tweet, subscribe_url, twitter_credentials):
    try:
        reply_tweet = f"subscribe now to read! {subscribe_url}"
        post_tweet(precta_tweet, **twitter_credentials, reply_text=reply_tweet)
    except Exception as e:
        logger.exception("Error while posting precta tweet:")
        raise


# Function to post post-newsletter tweet
def post_post_tweet(postcta_tweet, article_link, media_id, twitter_credentials):
    try:
        tweet_id = post_tweet(postcta_tweet, **twitter_credentials, media_id=media_id)
        reply_tweet = f"read the full article here: {article_link}"
        post_tweet(reply_tweet, **twitter_credentials, in_reply_to_tweet_id=tweet_id)
    except Exception as e:
        logger.exception("Error while posting postcta tweet:")
        raise


# Function to post a thread of tweets
def post_thread(thread_tweets, twitter_credentials):
    try:
        first_tweet_id = None
        previous_tweet_id = None

        for i, tweet in enumerate(thread_tweets):
            logger.info(f"Posting tweet {i+1}: {tweet}")  # Log each tweet content
            if i == 0:
                first_tweet_id = post_tweet(tweet, **twitter_credentials)
                previous_tweet_id = first_tweet_id
            else:
                previous_tweet_id = post_tweet(
                    tweet, **twitter_credentials, in_reply_to_tweet_id=previous_tweet_id
                )

        # Quote tweet the first tweet in the last tweet
        if first_tweet_id:
            last_tweet_text = f"and if you found this thread to be valuable, it would really help if you liked and shared! https://twitter.com/yourusername/status/{first_tweet_id}"
            post_tweet(
                last_tweet_text,
                **twitter_credentials,
                in_reply_to_tweet_id=previous_tweet_id,
            )
    except Exception as e:
        logger.exception("Error while posting thread:")
        raise


# Main function to run the script
def main(user_id, edition_url, generate_precta, generate_postcta, generate_thread):
    try:
        logger.info("Starting the main function")
        user_config = load_user_config(user_id)
        logger.info(f"Loaded user config: {json.dumps(user_config, indent=4)}")

        twitter_credentials = {
            "twitter_api_key": os.getenv(
                "TWITTER_API_KEY"
            ),  # Using environment variable
            "twitter_api_secret": os.getenv(
                "TWITTER_API_SECRET"
            ),  # Using environment variable
            "twitter_access_key": user_config["twitter_access_key"],
            "twitter_access_secret": user_config["twitter_access_secret"],
        }
        logger.info(f"Twitter credentials loaded for user: {user_id}")

        content_data = fetch_beehiiv_content(user_id, edition_url)
        logger.info(f"Fetched Beehiiv content: {json.dumps(content_data, indent=4)}")

        original_content = content_data["free_content"]

        article_link = content_data["web_url"]
        thumbnail_url = content_data["thumbnail_url"]
        subscribe_url = content_data["subscribe_url"]

        if generate_precta:
            precta_tweet = generate_precta_tweet(original_content, user_id)
            logger.info(f"Generated precta tweet: {precta_tweet}")
            post_pre_tweet(precta_tweet, subscribe_url, twitter_credentials)

        if generate_postcta:
            postcta_tweet = generate_postcta_tweet(original_content, user_id)
            logger.info(f"Generated postcta tweet: {postcta_tweet}")
            media_id = upload_media(
                thumbnail_url,
                twitter_credentials["twitter_api_key"],
                twitter_credentials["twitter_api_secret"],
                twitter_credentials["twitter_access_key"],
                twitter_credentials["twitter_access_secret"],
            )
            logger.info(f"Uploaded media with ID: {media_id}")
            post_post_tweet(postcta_tweet, article_link, media_id, twitter_credentials)

        if generate_thread:
            thread_tweets = generate_thread_tweets(
                original_content, article_link, user_id
            )
            logger.info(f"Generated thread tweets: {thread_tweets}")
            post_thread(thread_tweets, twitter_credentials)

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
