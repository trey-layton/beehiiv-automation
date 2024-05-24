from requests_oauthlib import OAuth1Session
import json
import logging
import requests
import tempfile
import os
import time

logger = logging.getLogger(__name__)


def upload_media(
    media_url,
    twitter_api_key,
    twitter_api_secret,
    twitter_access_key,
    twitter_access_secret,
):
    try:
        response = requests.get(media_url)
        if response.status_code != 200:
            raise Exception(
                f"Failed to download media: {response.status_code} {response.text}"
            )

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        twitter_oauth = OAuth1Session(
            twitter_api_key,
            client_secret=twitter_api_secret,
            resource_owner_key=twitter_access_key,
            resource_owner_secret=twitter_access_secret,
        )

        with open(temp_file_path, "rb") as file:
            media_data = file.read()

        response = twitter_oauth.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            files={"media": media_data},
        )

        if response.status_code != 200:
            raise Exception(
                f"Media upload returned an error: {response.status_code} {response.text}"
            )

        media_id = json.loads(response.text)["media_id_string"]
        logger.info("Media uploaded successfully!")

        return media_id
    except Exception as e:
        logger.exception("Error while uploading media:")
        raise
    finally:
        try:
            os.remove(temp_file_path)
        except Exception as cleanup_error:
            logger.exception("Error cleaning up temporary file:")


def post_tweet(
    tweet_text,
    twitter_api_key,
    twitter_api_secret,
    twitter_access_key,
    twitter_access_secret,
    reply_text=None,
    media_id=None,
    in_reply_to_tweet_id=None,
    max_retries=5,
):
    try:
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

        for attempt in range(max_retries):
            response = twitter_oauth.post(
                "https://api.twitter.com/2/tweets", json=payload
            )

            if response.status_code == 201:
                logger.info("Tweet posted successfully!")
                json_response = response.json()
                tweet_id = json_response["data"]["id"]

                if reply_text:
                    payload = {
                        "text": reply_text,
                        "reply": {"in_reply_to_tweet_id": tweet_id},
                    }
                    response = twitter_oauth.post(
                        "https://api.twitter.com/2/tweets", json=payload
                    )

                    if response.status_code != 201:
                        raise Exception(
                            f"Request returned an error: {response.status_code} {response.text}"
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
                    f"Request returned an error: {response.status_code} {response.text}"
                )

        raise Exception(
            f"Max retries exceeded. Request returned an error: {response.status_code} {response.text}"
        )

    except Exception as e:
        logger.exception("Error while posting tweet:")
        raise
