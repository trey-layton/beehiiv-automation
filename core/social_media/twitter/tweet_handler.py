# core/social_media/twitter/tweet_handler.py

import logging
from typing import Dict, List, Optional
from requests_oauthlib import OAuth1Session
import json
import time

logger = logging.getLogger(__name__)


class TweetHandler:
    def __init__(self, twitter_credentials: Dict[str, str]):
        logger.debug("Initializing TweetHandler")

        self.twitter_oauth = OAuth1Session(
            twitter_credentials["twitter_api_key"],
            client_secret=twitter_credentials["twitter_api_secret"],
            resource_owner_key=twitter_credentials["twitter_access_key"],
            resource_owner_secret=twitter_credentials["twitter_access_secret"],
        )
        logger.debug("TweetHandler initialized")

    def extract_tweet_text(self, tweet_content):
        if isinstance(tweet_content, str):
            try:
                # Try to parse as JSON
                tweet_data = json.loads(tweet_content)
                if isinstance(tweet_data, dict) and "tweet" in tweet_data:
                    return tweet_data["tweet"]
            except json.JSONDecodeError:
                # If it's not valid JSON, return the original string
                pass
        return tweet_content

    def post_tweet(
        self,
        tweet_text: str,
        media_id: Optional[str] = None,
        in_reply_to_tweet_id: Optional[str] = None,
        quote_tweet_id: Optional[str] = None,
        max_retries: int = 5,
    ) -> Optional[str]:
        logger.debug(f"Posting tweet: {tweet_text[:50]}...")

        payload = {"text": tweet_text}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        if in_reply_to_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": in_reply_to_tweet_id}
        if quote_tweet_id:
            payload["quote_tweet_id"] = quote_tweet_id

        for attempt in range(max_retries):
            try:
                response = self.twitter_oauth.post(
                    "https://api.twitter.com/2/tweets", json=payload
                )
                if response.status_code == 201:
                    json_response = response.json()
                    return json_response["data"]["id"]
                elif response.status_code == 429:
                    wait_time = (2**attempt) * 10
                    logger.warning(
                        f"Rate limit exceeded. Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Tweet post failed: {response.status_code} {response.text}"
                    )
                    return None
            except Exception as e:
                logger.exception(f"Error posting tweet (attempt {attempt + 1}):")

        logger.error("Max retries exceeded for posting tweet")
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

    def post_thread(self, tweets: List[str], article_url: str) -> None:
        logger.debug(f"Posting thread with {len(tweets)} tweets")
        previous_tweet_id = None
        first_tweet_id = None
        for i, tweet in enumerate(tweets):
            tweet_id = self.post_tweet(tweet, in_reply_to_tweet_id=previous_tweet_id)
            if not tweet_id:
                logger.error(f"Failed to post thread tweet {i+1}")
                return
            if i == 0:
                first_tweet_id = tweet_id
            previous_tweet_id = tweet_id

        if previous_tweet_id:
            article_tweet = f"if you want to go even deeper, check out the full article! {article_url}"
            logger.debug(f"Posting article link tweet: {article_tweet}")
            article_tweet_id = self.post_tweet(
                article_tweet, in_reply_to_tweet_id=previous_tweet_id
            )

            if article_tweet_id:
                quote_tweet = "and if you found value in this thread, please give it a like and share!"
                logger.debug(f"Posting quote tweet: {quote_tweet}")
                self.post_tweet(
                    quote_tweet,
                    in_reply_to_tweet_id=article_tweet_id,
                    quote_tweet_id=first_tweet_id,
                )
            else:
                logger.error("Failed to post article link tweet")
        else:
            logger.error("Failed to post any thread tweets")


# Usage in main_process.py remains the same as in the previous example
