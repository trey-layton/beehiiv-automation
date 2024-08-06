import requests
from requests_oauthlib import OAuth1Session
import json
import logging
from typing import Optional, List, Dict, Union
from media_upload import upload_media, advanced_upload_media

logger = logging.getLogger(__name__)


class TweetHandler:
    def __init__(self, user_config: dict):
        self.user_config = user_config
        self.oauth = OAuth1Session(
            user_config["twitter_api_key"],
            client_secret=user_config["twitter_api_secret"],
            resource_owner_key=user_config["twitter_access_key"],
            resource_owner_secret=user_config["twitter_access_secret"],
        )
        self.user_id = user_config.get("id")

    def initialize_twitter_oauth(self):
        if not self.user_id:
            raise ValueError("User ID not set. Please set user_id before initializing.")
        logger.debug("TweetHandler initialized")

    def post_tweet(
        self,
        tweet_text: str,
        media_id: Optional[str] = None,
        in_reply_to_tweet_id: Optional[str] = None,
        quote_tweet_id: Optional[str] = None,
    ) -> Optional[str]:
        url = "https://api.twitter.com/2/tweets"

        payload = {"text": tweet_text}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        if in_reply_to_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": in_reply_to_tweet_id}
        if quote_tweet_id:
            payload["quote_tweet_id"] = quote_tweet_id

        headers = {"Content-Type": "application/json"}

        logger.debug(f"Posting tweet: {tweet_text}")
        logger.debug(f"Tweet payload: {json.dumps(payload, indent=2)}")

        try:
            response = self.oauth.post(url, headers=headers, json=payload)
            logger.debug(
                f"Twitter API response: Status {response.status_code}, Content: {response.text}"
            )

            if response.status_code != 201:
                logger.error(
                    f"Error posting tweet. Status: {response.status_code}, Response: {response.text}"
                )
                return None

            json_response = response.json()
            logger.info(f"Tweet posted successfully: {json_response['data']['text']}")
            return json_response["data"]["id"]
        except Exception as e:
            logger.exception(f"Error posting tweet: {str(e)}")
            return None

    def post_pre_cta_tweet(self, precta_tweet: str, subscribe_url: str) -> None:
        logger.debug(f"Posting pre-CTA tweet: {precta_tweet}")
        tweet_id = self.post_tweet(precta_tweet)
        if tweet_id:
            reply_tweet = f"subscribe for free to get it in your inbox! {subscribe_url}"
            logger.debug(f"Posting pre-CTA reply: {reply_tweet}")
            self.post_tweet(reply_tweet, in_reply_to_tweet_id=tweet_id)
        else:
            logger.error("Failed to post pre-CTA tweet")

    def post_post_cta_tweet(
        self, postcta_tweet: str, article_link: str, media_id: str
    ) -> None:
        logger.debug(f"Posting post-CTA tweet: {postcta_tweet}")
        tweet_id = self.post_tweet(postcta_tweet, media_id=media_id)
        if tweet_id:
            reply_tweet = f"check out the full thing online now! {article_link}"
            logger.debug(f"Posting post-CTA reply: {reply_tweet}")
            self.post_tweet(reply_tweet, in_reply_to_tweet_id=tweet_id)
        else:
            logger.error("Failed to post post-CTA tweet")

    def post_thread(
        self, tweets: List[Union[str, Dict[str, str]]], article_url: str
    ) -> None:
        logger.debug(f"Posting thread with {len(tweets)} tweets")
        previous_tweet_id = None
        first_tweet_id = None

        for i, tweet in enumerate(tweets):
            if isinstance(tweet, dict):
                tweet_text = tweet.get("text", "")
                tweet_type = tweet.get("type", "normal")
            else:
                tweet_text = str(tweet)
                tweet_type = "normal"

            logger.debug(
                f"Posting tweet {i+1}: {tweet_text[:50]}... (Type: {tweet_type})"
            )

            if not tweet_text:
                logger.warning(f"Empty tweet detected at position {i+1}. Skipping.")
                continue

            try:
                if tweet_type == "quote_tweet":
                    tweet_id = self.post_tweet(
                        tweet_text,
                        in_reply_to_tweet_id=previous_tweet_id,
                        quote_tweet_id=first_tweet_id,
                    )
                else:
                    tweet_id = self.post_tweet(
                        tweet_text, in_reply_to_tweet_id=previous_tweet_id
                    )

                if not tweet_id:
                    logger.error(f"Failed to post thread tweet {i+1}")
                    return

                logger.debug(f"Tweet {i+1} posted successfully with ID: {tweet_id}")

                if i == 0:
                    first_tweet_id = tweet_id
                    logger.debug(f"First tweet ID captured: {first_tweet_id}")

                previous_tweet_id = tweet_id

            except Exception as e:
                logger.exception(f"Error posting tweet {i+1}: {str(e)}")
                return

        logger.info("Thread posted successfully")

    def upload_media(self, media_url: str) -> Optional[str]:
        return upload_media(media_url, self.user_config)

    def advanced_upload_media(self, media_url: str) -> Optional[str]:
        return advanced_upload_media(media_url, self.user_config)
