import os
import logging
from typing import Dict, List, Optional, Union
import requests
from requests_oauthlib import OAuth1, OAuth1Session
import json
import time
from core.config.user_config import load_user_config
from core.encryption.encryption import get_key
from dotenv import load_dotenv
import asyncio
import aiohttp


logger = logging.getLogger(__name__)


class TweetHandler:
    def __init__(self, twitter_credentials):
        self.oauth = OAuth1(
            twitter_credentials["twitter_api_key"],
            client_secret=twitter_credentials["twitter_api_secret"],
            resource_owner_key=twitter_credentials["twitter_access_key"],
            resource_owner_secret=twitter_credentials["twitter_access_secret"],
        )
        self.user_id = None

    def set_user_id(self, user_id: str):
        self.user_id = user_id

    def initialize_twitter_oauth(self):
        if not self.user_id:
            raise ValueError("User ID not set. Please set user_id before initializing.")
        # The OAuth1 session is already initialized in the constructor, so we don't need to do anything here
        logger.debug("TweetHandler initialized")

        user_data = load_user_config(self.user_id)
        if not user_data:
            raise ValueError(f"Failed to get user data for user {self.user_id}")

        twitter_api_key = os.getenv("TWITTER_API_KEY")
        twitter_api_secret = os.getenv("TWITTER_API_SECRET")
        twitter_access_key = user_data.get("twitter_access_key")
        twitter_access_secret = user_data.get("twitter_access_secret")

        if not all(
            [
                twitter_api_key,
                twitter_api_secret,
                twitter_access_key,
                twitter_access_secret,
            ]
        ):
            raise ValueError("Missing Twitter API credentials")

        self.twitter_oauth = OAuth1Session(
            twitter_api_key,
            client_secret=twitter_api_secret,
            resource_owner_key=twitter_access_key,
            resource_owner_secret=twitter_access_secret,
        )
        logger.debug("TweetHandler initialized")

    async def upload_media(self, media_url: str) -> Optional[str]:
        if not self.twitter_oauth:
            raise ValueError(
                "Twitter OAuth not initialized. Call initialize_twitter_oauth first."
            )

        try:
            response = requests.get(media_url)
            if response.status_code != 200:
                raise Exception(
                    f"Failed to download media: {response.status_code} {response.text}"
                )

            media_content = response.content

            # INIT
            init_url = "https://upload.twitter.com/1.1/media/upload.json"
            init_data = {
                "command": "INIT",
                "total_bytes": len(media_content),
                "media_type": response.headers.get("Content-Type", "image/jpeg"),
            }
            init_response = self.twitter_oauth.post(init_url, data=init_data)
            if init_response.status_code != 202:
                raise Exception(
                    f"Failed to initialize upload: {init_response.status_code} {init_response.text}"
                )

            media_id = init_response.json()["media_id_string"]

            # APPEND
            append_url = "https://upload.twitter.com/1.1/media/upload.json"
            segment_size = 4 * 1024 * 1024  # 4MB chunks
            for segment_index in range(0, len(media_content), segment_size):
                chunk = media_content[segment_index : segment_index + segment_size]
                append_data = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_index // segment_size,
                }
                files = {"media": chunk}
                append_response = self.twitter_oauth.post(
                    append_url, data=append_data, files=files
                )
                if append_response.status_code != 204:
                    raise Exception(
                        f"Failed to append media chunk: {append_response.status_code} {append_response.text}"
                    )

            # FINALIZE
            finalize_url = "https://upload.twitter.com/1.1/media/upload.json"
            finalize_data = {"command": "FINALIZE", "media_id": media_id}
            finalize_response = self.twitter_oauth.post(
                finalize_url, data=finalize_data
            )
            if finalize_response.status_code != 201:
                raise Exception(
                    f"Failed to finalize upload: {finalize_response.status_code} {finalize_response.text}"
                )

            logger.info("Media uploaded successfully!")
            return media_id

        except Exception as e:
            logger.exception("Error while uploading media:")
            return None

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
            response = requests.post(
                url, auth=self.oauth, headers=headers, json=payload
            )
            logger.debug(
                f"Twitter API response: Status {response.status_code}, Content: {response.text}"
            )

            if response.status_code != 201:
                raise Exception(
                    f"Request returned an error: {response.status_code} {response.text}"
                )

            json_response = response.json()
            logger.info(f"Tweet posted successfully: {json_response['data']['text']}")
            return json_response["data"]["id"]
        except Exception as e:
            logger.exception(f"Error posting tweet: {str(e)}")
            return None

    async def post_pre_cta_tweet(self, precta_tweet: str, subscribe_url: str) -> None:
        logger.debug(f"Posting pre-CTA tweet: {precta_tweet}")
        tweet_id = await self.post_tweet(precta_tweet)
        if tweet_id:
            reply_tweet = f"subscribe for free to get it in your inbox! {subscribe_url}"
            logger.debug(f"Posting pre-CTA reply: {reply_tweet}")
            await self.post_tweet(reply_tweet, in_reply_to_tweet_id=tweet_id)
        else:
            logger.error("Failed to post pre-CTA tweet")

    async def post_post_cta_tweet(
        self, postcta_tweet: str, article_link: str, media_id: str
    ) -> None:
        logger.debug(f"Posting post-CTA tweet: {postcta_tweet}")
        tweet_id = await self.post_tweet(postcta_tweet, media_id=media_id)
        if tweet_id:
            reply_tweet = f"check out the full thing online now! {article_link}"
            logger.debug(f"Posting post-CTA reply: {reply_tweet}")
            await self.post_tweet(reply_tweet, in_reply_to_tweet_id=tweet_id)
        else:
            logger.error("Failed to post post-CTA tweet")

    async def post_thread(
        self, tweets: List[Union[str, Dict[str, str]]], article_url: str
    ) -> None:
        logger.debug(f"Posting thread with {len(tweets)} tweets")
        previous_tweet_id = None
        first_tweet_id = None

        for i, tweet in enumerate(tweets):
            if isinstance(tweet, dict):
                tweet_text = tweet["text"]
                tweet_type = tweet.get("type", "normal")
            else:
                tweet_text = tweet
                tweet_type = "normal"

            logger.debug(f"Posting tweet {i+1}: {tweet_text[:50]}...")

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

            # Add a delay between tweets to avoid rate limiting
            await asyncio.sleep(2)

        logger.info("Thread posted successfully")
