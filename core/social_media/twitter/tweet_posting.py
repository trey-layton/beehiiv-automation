from requests_oauthlib import OAuth1Session
import requests
import logging
import time
from typing import Optional, List, Dict
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def post_tweet(
    tweet_text: str,
    twitter_credentials: Dict[str, str],
    reply_text: Optional[str] = None,
    media_id: Optional[str] = None,
    in_reply_to_tweet_id: Optional[str] = None,
    max_retries: int = 5,
) -> str:
    try:
        twitter_api_key = twitter_credentials["twitter_api_key"]
        twitter_api_secret = twitter_credentials["twitter_api_secret"]
        twitter_access_key = twitter_credentials["twitter_access_key"]
        twitter_access_secret = twitter_credentials["twitter_access_secret"]

        twitter_oauth = OAuth1Session(
            twitter_api_key,
            client_secret=twitter_api_secret,
            resource_owner_key=twitter_access_key,
            resource_owner_secret=twitter_access_secret,
        )

        payload = {"text": tweet_text}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        if in_reply_to_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": in_reply_to_tweet_id}

        logger.debug(
            f"Preparing to post tweet with payload: {json.dumps(payload, indent=2)}"
        )

        for attempt in range(max_retries):
            logger.info(f"Attempt {attempt + 1} of {max_retries} to post tweet")
            response = twitter_oauth.post(
                "https://api.twitter.com/2/tweets", json=payload
            )

            logger.debug(f"API Response Status Code: {response.status_code}")
            logger.debug(
                f"API Response Headers: {json.dumps(dict(response.headers), indent=2)}"
            )
            logger.debug(f"API Response Content: {response.text}")

            if response.status_code == 201:
                logger.info("Tweet posted successfully!")
                json_response = response.json()
                tweet_id = json_response["data"]["id"]

                if reply_text:
                    logger.info(f"Posting reply tweet: {reply_text}")
                    payload = {
                        "text": reply_text,
                        "reply": {"in_reply_to_tweet_id": tweet_id},
                    }
                    response = twitter_oauth.post(
                        "https://api.twitter.com/2/tweets", json=payload
                    )

                    logger.debug(
                        f"Reply API Response Status Code: {response.status_code}"
                    )
                    logger.debug(
                        f"Reply API Response Headers: {json.dumps(dict(response.headers), indent=2)}"
                    )
                    logger.debug(f"Reply API Response Content: {response.text}")

                    if response.status_code != 201:
                        raise Exception(
                            f"Reply tweet returned an error: {response.status_code} {response.text}"
                        )

                    logger.info("Reply tweet posted successfully!")

                return tweet_id

            elif response.status_code == 429:
                wait_time = (2**attempt) * 10
                logger.warning(
                    f"Rate limit exceeded. Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
            else:
                raise Exception(
                    f"Tweet post returned an error: {response.status_code} {response.text}"
                )

        raise Exception(
            f"Max retries exceeded. Final error: {response.status_code} {response.text}"
        )

    except requests.RequestException as e:
        logger.error(f"Network error while posting tweet: {e}")
        raise
    except Exception as e:
        logger.exception("Error while posting tweet:")
        raise


def post_pre_tweet(
    precta_tweet: str, subscribe_url: str, twitter_credentials: Dict[str, str]
) -> None:
    """
    Posts a pre-newsletter tweet with a subscription link.

    Args:
        precta_tweet (str): The content of the pre-newsletter tweet.
        subscribe_url (str): The subscription URL to include in the tweet.
        twitter_credentials (Dict[str, str]): Twitter API credentials.

    Raises:
        Exception: If an error occurs during posting.
    """
    try:
        reply_tweet = f"subscribe now to read! {subscribe_url}"
        post_tweet(precta_tweet, twitter_credentials, reply_text=reply_tweet)
    except Exception as e:
        logger.exception("Error while posting precta tweet:")
        raise


def post_post_tweet(
    postcta_tweet: str,
    article_link: str,
    media_id: str,
    twitter_credentials: Dict[str, str],
) -> None:
    """
    Posts a post-newsletter tweet with an article link and media.

    Args:
        postcta_tweet (str): The content of the post-newsletter tweet.
        article_link (str): The URL of the full article.
        media_id (str): The ID of the uploaded media.
        twitter_credentials (Dict[str, str]): Twitter API credentials.

    Raises:
        Exception: If an error occurs during posting.
    """
    try:
        tweet_id = post_tweet(postcta_tweet, twitter_credentials, media_id=media_id)
        reply_tweet = f"read the full article here: {article_link}"
        post_tweet(reply_tweet, twitter_credentials, in_reply_to_tweet_id=tweet_id)
    except Exception as e:
        logger.exception("Error while posting postcta tweet:")
        raise


def post_thread(thread_tweets: List[str], twitter_credentials: Dict[str, str]) -> None:
    """
    Posts a thread of tweets.

    Args:
        thread_tweets (List[str]): A list of tweets to post as a thread.
        twitter_credentials (Dict[str, str]): Twitter API credentials.

    Raises:
        Exception: If an error occurs during posting.
    """
    try:
        first_tweet_id: Optional[str] = None
        previous_tweet_id: Optional[str] = None

        for i, tweet in enumerate(thread_tweets):
            logger.info(f"Posting tweet {i+1}: {tweet}")
            if i == 0:
                first_tweet_id = post_tweet(tweet, twitter_credentials)
                previous_tweet_id = first_tweet_id
            else:
                previous_tweet_id = post_tweet(
                    tweet, twitter_credentials, in_reply_to_tweet_id=previous_tweet_id
                )

        if first_tweet_id:
            last_tweet_text = f"and if you found this thread to be valuable, it would really help if you liked and shared! https://twitter.com/yourusername/status/{first_tweet_id}"
            post_tweet(
                last_tweet_text,
                twitter_credentials,
                in_reply_to_tweet_id=previous_tweet_id,
            )
    except Exception as e:
        logger.exception("Error while posting thread:")
        raise
