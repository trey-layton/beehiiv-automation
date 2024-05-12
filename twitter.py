from requests_oauthlib import OAuth1Session
import json
from config import get_config
import logging

logger = logging.getLogger(__name__)


def post_tweet(tweet_text):
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
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )

        logger.info("Tweet posted successfully!")
        logger.info("Response code: {}".format(response.status_code))

        json_response = response.json()
        logger.debug(json.dumps(json_response, indent=4, sort_keys=True))
    except Exception as e:
        logger.exception("Error while posting tweet:")
        raise
