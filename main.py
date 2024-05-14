import logging
import json
import schedule
import time
from beehiiv import get_beehiiv_post_id, get_beehiiv_post_content
from content_extraction import extract_text
from content_generation import generate_article_tweets
from twitter import post_tweet
from config import load_env_variables, get_config
from dotenv import load_dotenv


def load_env_variables():
    load_dotenv(dotenv_path="/Users/treylayton/Desktop/Coding/beehiiv_project/.env")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_beehiiv_content(user_id):
    try:
        config = get_config()
        with open("user_config.json") as f:
            user_config = json.load(f)

        beehiiv_api_key = user_config[user_id]["beehiiv_api_key"]
        beehiiv_url = user_config[user_id]["beehiiv_url"]

        post_id = get_beehiiv_post_id(beehiiv_url)
        content_data = get_beehiiv_post_content(
            beehiiv_api_key, config["publication_id"], post_id
        )

        return content_data
    except Exception as e:
        logger.exception("Error while fetching Beehiiv content:")
        raise


def post_on_twitter(precta_tweet, postcta_tweet, subscribe_url, post_tweet_flag):
    try:
        if post_tweet_flag:
            # Post the precta tweet
            logger.info("precta tweet:")
            logger.info(precta_tweet)
            reply_tweet = f"Subscribe now to read! {subscribe_url}"
            post_tweet(precta_tweet, reply_tweet)

            # Schedule the post cta tweet
            def post_postcta_tweet():
                logger.info("post cta Tweet:")
                logger.info(postcta_tweet)
                post_tweet(postcta_tweet, "")

            # Schedule the post cta tweet to be posted after a certain delay
            schedule_time = 10  # Delay in minutes, adjust as needed
            schedule.every(schedule_time).minutes.do(post_postcta_tweet)

            while True:
                schedule.run_pending()
                time.sleep(1)

    except Exception as e:
        logger.exception("Error while posting tweet:")
        raise


def main(user_id, post_tweet_flag=True):
    try:
        load_env_variables()
        config = get_config()
        subscribe_url = config["subscribe_url"]

        content_data = fetch_beehiiv_content(user_id)
        cleaned_text = extract_text(content_data["free_content"])
        logger.info("Cleaned text:")
        logger.info(cleaned_text)

        article_link = content_data["web_url"]
        precta_tweet, postcta_tweet = generate_article_tweets(
            cleaned_text, article_link
        )

        post_on_twitter(precta_tweet, postcta_tweet, subscribe_url, post_tweet_flag)
    except Exception as e:
        logger.exception("An error occurred:")
        return None


if __name__ == "__main__":
    user_id = input("Enter the user ID: ")
    post_tweet_flag = (
        input("Do you want to post the tweet? (yes/no): ").strip().lower() == "yes"
    )
    main(user_id, post_tweet_flag)
