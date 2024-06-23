import logging
from typing import Dict, List, Optional
from core.social_media.twitter.tweet_posting import post_tweet

logger = logging.getLogger(__name__)


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
