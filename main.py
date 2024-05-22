import logging
import json
import time
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


def load_env_variables():
    load_dotenv(dotenv_path="/Users/treylayton/Desktop/Coding/beehiiv_project/.env")


def get_user_config():
    with open("user_config.json") as config_file:
        return json.load(config_file)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_beehiiv_content(user_id):
    try:
        user_config = get_user_config()

        beehiiv_api_key = user_config[user_id]["beehiiv_api_key"]
        beehiiv_url = user_config[user_id]["beehiiv_url"]
        subscribe_url = user_config[user_id]["subscribe_url"]
        publication_id = user_config[user_id]["publication_id"]

        post_id = get_beehiiv_post_id(beehiiv_url)
        content_data = get_beehiiv_post_content(
            beehiiv_api_key, publication_id, post_id
        )
        content_data["subscribe_url"] = subscribe_url

        return content_data
    except Exception as e:
        logger.exception("Error while fetching Beehiiv content:")
        raise


def post_pre_tweet(precta_tweet, subscribe_url):
    try:
        reply_tweet = f"subscribe now to read! {subscribe_url}"
        post_tweet(precta_tweet, reply_text=reply_tweet)
    except Exception as e:
        logger.exception("Error while posting precta tweet:")
        raise


def post_post_tweet(postcta_tweet, article_link, media_id):
    try:
        tweet_id = post_tweet(postcta_tweet, media_id=media_id)
        reply_tweet = f"read the full article here: {article_link}"
        post_tweet(reply_tweet, in_reply_to_tweet_id=tweet_id)
    except Exception as e:
        logger.exception("Error while posting postcta tweet:")
        raise


def post_thread(thread_tweets):
    try:
        first_tweet_id = None
        previous_tweet_id = None

        for i, tweet in enumerate(thread_tweets):
            logger.info(f"Posting tweet {i+1}: {tweet}")  # Log each tweet content
            if i == 0:
                first_tweet_id = post_tweet(tweet)
                previous_tweet_id = first_tweet_id
            else:
                previous_tweet_id = post_tweet(
                    tweet, in_reply_to_tweet_id=previous_tweet_id
                )

        # Quote tweet the first tweet in the last tweet
        if first_tweet_id:
            last_tweet_text = f"and if you found this thread to be valuable, it would really help if you liked and shared! https://twitter.com/yourusername/status/{first_tweet_id}"
            post_tweet(last_tweet_text, in_reply_to_tweet_id=previous_tweet_id)
    except Exception as e:
        logger.exception("Error while posting thread:")
        raise


def main(user_id, generate_precta, generate_postcta, generate_thread):
    try:
        load_env_variables()
        user_config = get_user_config()

        content_data = fetch_beehiiv_content(user_id)
        logger.info(f"Fetched Beehiiv content: {json.dumps(content_data, indent=4)}")

        original_content = content_data["free_content"]

        article_link = content_data["web_url"]
        thumbnail_url = content_data["thumbnail_url"]
        subscribe_url = content_data["subscribe_url"]

        if generate_precta:
            precta_tweet = generate_precta_tweet(original_content)
            post_pre_tweet(precta_tweet, subscribe_url)

        if generate_postcta:
            postcta_tweet = generate_postcta_tweet(original_content)
            media_id = upload_media(thumbnail_url)
            post_post_tweet(postcta_tweet, article_link, media_id)

        if generate_thread:
            thread_tweets = generate_thread_tweets(original_content, article_link)
            for tweet in thread_tweets:
                print(tweet)
            post_thread(thread_tweets)

    except Exception as e:
        logger.exception("An error occurred:")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate and post tweets from Beehiiv content."
    )
    parser.add_argument("user_id", help="User ID for fetching Beehiiv content")
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

    main(args.user_id, args.precta, args.postcta, args.thread)
