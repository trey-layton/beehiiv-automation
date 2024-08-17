import logging
from typing import Any, Dict, Tuple
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.content.improved_llm_flow.content_editor import edit_content
from core.social_media.twitter.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweet,
    generate_long_form_tweet,
)
from core.social_media.linkedin.generate_linkedin_post import generate_linkedin_post

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile, post_id: str, content_type: str
) -> Tuple[bool, str, Dict[str, Any]]:
    logger.info(f"run_main_process started for user {account_profile.account_id}")
    try:
        logger.info(f"Fetching Beehiiv content for Post: {post_id}")
        content_data = await fetch_beehiiv_content(account_profile, post_id)
        original_content = content_data.get("free_content")
        web_url = content_data.get("web_url")

        if not original_content or not web_url:
            logger.error("Failed to fetch content or web URL from Beehiiv")
            return False, "Failed to fetch content or web URL from Beehiiv", {}

        generated_content = {}

        if content_type == "precta_tweet":
            precta_tweets = await generate_precta_tweet(
                original_content, account_profile
            )
            edited_tweets = [
                {
                    "type": tweet["type"],
                    "text": await edit_content(
                        tweet["text"], f"pre-CTA {tweet['type']}"
                    ),
                }
                for tweet in precta_tweets
            ]
            generated_content = {
                "provider": "twitter",
                "type": "precta_tweet",
                "content": edited_tweets,
            }

        elif content_type == "postcta_tweet":
            postcta_tweets = await generate_postcta_tweet(
                original_content, account_profile, web_url
            )
            edited_tweets = [
                {
                    "type": tweet["type"],
                    "text": await edit_content(
                        tweet["text"], f"post-CTA {tweet['type']}"
                    ),
                }
                for tweet in postcta_tweets
            ]
            generated_content = {
                "provider": "twitter",
                "type": "postcta_tweet",
                "content": edited_tweets,
            }

        if content_type == "thread_tweet":
            from core.social_media.twitter.generate_tweets import generate_thread_tweet

            thread_tweet = await generate_thread_tweet(
                original_content, content_data.get("web_url"), account_profile
            )

            # Edit the entire thread as a single piece of content
            thread_text = "\n\n".join([tweet["text"] for tweet in thread_tweet])
            edited_thread_text = await edit_content(thread_text, "thread tweet")

            # Split the edited thread back into individual tweets
            edited_tweets = edited_thread_text.split("\n\n")

            edited_thread = []
            for i, tweet_text in enumerate(edited_tweets):
                if i < len(thread_tweet):
                    edited_thread.append(
                        {"type": thread_tweet[i]["type"], "text": tweet_text.strip()}
                    )
                else:
                    edited_thread.append(
                        {"type": "content", "text": tweet_text.strip()}
                    )

            generated_content = {
                "provider": "twitter",
                "type": "thread_tweet",
                "content": edited_thread,
            }

        elif content_type == "long_form_tweet":
            long_form_tweet = await generate_long_form_tweet(
                original_content, account_profile
            )
            edited_tweet = await edit_content(long_form_tweet, "long-form tweet")
            generated_content = {
                "provider": "twitter",
                "type": "long_form_tweet",
                "content": [{"type": "long_post", "text": edited_tweet}],
            }

        elif content_type == "linkedin":
            linkedin_post = await generate_linkedin_post(
                original_content, account_profile
            )
            edited_post = await edit_content(linkedin_post, "LinkedIn post")
            generated_content = {
                "provider": "linkedin",
                "type": "linkedin",
                "content": [{"type": "post", "text": edited_post}],
            }

        logger.info("Content generation and editing completed successfully")
        return True, "Content generated and edited successfully", generated_content

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
