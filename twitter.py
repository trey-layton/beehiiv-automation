from requests_oauthlib import OAuth1Session
import json
import logging
from config import get_config

logger = logging.getLogger(__name__)


def post_tweet(tweet_text, reply_text):
    try:
        config = get_config()
        twitter_oauth = OAuth1Session(
            config["twitter_api_key"],
            client_secret=config["twitter_api_secret"],
            resource_owner_key=config["twitter_access_key"],
            resource_owner_secret=config["twitter_access_secret"],
        )

        payload = {"text": tweet_text}
        response = twitter_oauth.post("https://api.twitter.com/2/tweets", json=payload)

        if response.status_code != 201:
            raise Exception(
                f"Request returned an error: {response.status_code} {response.text}"
            )

        logger.info("Main tweet posted successfully!")
        json_response = response.json()
        tweet_id = json_response["data"]["id"]

        payload = {"text": reply_text, "reply": {"in_reply_to_tweet_id": tweet_id}}
        response = twitter_oauth.post("https://api.twitter.com/2/tweets", json=payload)

        if response.status_code != 201:
            raise Exception(
                f"Request returned an error: {response.status_code} {response.text}"
            )

        logger.info("Reply tweet posted successfully!")
    except Exception as e:
        logger.exception("Error while posting tweet:")
        raise
