import logging
import json
import time
import os
from dotenv import load_dotenv
from beehiiv import get_beehiiv_post_id, get_beehiiv_post_content
from content_extraction import extract_text
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
        reply_tweet = f"Subscribe now to read! {subscribe_url}"
        post_tweet(precta_tweet, reply_text=reply_tweet)
    except Exception as e:
        logger.exception("Error while posting precta tweet:")
        raise


def post_post_tweet(postcta_tweet, article_link, media_id):
    try:
        tweet_id = post_tweet(postcta_tweet, media_id=media_id)
        reply_tweet = f"Read the full article here: {article_link}"
        post_tweet(reply_tweet, in_reply_to_tweet_id=tweet_id)
    except Exception as e:
        logger.exception("Error while posting postcta tweet:")
        raise


def post_thread(thread_tweets):
    try:
        first_tweet_id = None
        previous_tweet_id = None

        for i, tweet in enumerate(thread_tweets):
            if i == 0:
                first_tweet_id = post_tweet(tweet)
                previous_tweet_id = first_tweet_id
            else:
                previous_tweet_id = post_tweet(
                    tweet, in_reply_to_tweet_id=previous_tweet_id
                )

        # Quote tweet the first tweet in the last tweet
        if first_tweet_id:
            last_tweet_text = (
                f"Quote tweet: https://twitter.com/yourusername/status/{first_tweet_id}"
            )
            post_tweet(last_tweet_text, in_reply_to_tweet_id=previous_tweet_id)
    except Exception as e:
        logger.exception("Error while posting thread:")
        raise


def main(user_id, post_tweet_flag=True):
    try:
        load_env_variables()
        user_config = get_user_config()

        content_data = fetch_beehiiv_content(user_id)
        cleaned_text = extract_text(content_data["free_content"])
        logger.info("Cleaned text:")
        logger.info(cleaned_text)

        article_link = content_data["web_url"]
        thumbnail_url = content_data["thumbnail_url"]
        subscribe_url = content_data["subscribe_url"]

        precta_tweet = generate_precta_tweet(cleaned_text)
        postcta_tweet = generate_postcta_tweet(cleaned_text)
        thread_tweets = generate_thread_tweets(cleaned_text, subscribe_url)

        if post_tweet_flag:
            # post_pre_tweet(precta_tweet, subscribe_url)
            time.sleep(5)  # Short delay in seconds
            media_id = upload_media(thumbnail_url)
            # post_post_tweet(postcta_tweet, article_link, media_id)
            post_thread(thread_tweets)

    except Exception as e:
        logger.exception("An error occurred:")
        return None


if __name__ == "__main__":
    user_id = input("Enter the user ID: ")
    post_tweet_flag = (
        input("Do you want to post the tweet? (yes/no): ").strip().lower() == "yes"
    )
    main(user_id, post_tweet_flag)
