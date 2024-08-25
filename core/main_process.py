import logging
from typing import Any, Dict, Tuple
import os
import supabase
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.content.improved_llm_flow.content_editor import edit_content
from core.social_media.twitter.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweet,
    generate_long_form_tweet,
    format_tweet_with_link,
)
from core.social_media.linkedin.generate_linkedin_post import generate_linkedin_post
from core.content.image_generator import generate_image_list, edit_image_list_content

from core.utils.storage_utils import upload_to_supabase

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    post_id: str,
    content_type: str,
    supabase: supabase.Client,
) -> Tuple[bool, str, Dict[str, Any]]:
    logger.info(
        f"run_main_process started for user {account_profile.account_id} with content_type: {content_type}"
    )
    try:
        logger.info(f"Fetching Beehiiv content for Post: {post_id}")
        content_data = await fetch_beehiiv_content(account_profile, post_id, supabase)
        original_content = content_data.get("free_content")
        web_url = content_data.get("web_url")

        if not original_content or not web_url:
            logger.error("Failed to fetch content or web URL from Beehiiv")
            return False, "Failed to fetch content or web URL from Beehiiv", {}

        generated_content = {}
        if content_type == "image_list":
            logger.info(f"Generating image list content for post {post_id}")
            image_list_content = await generate_image_list(
                original_content, account_profile
            )
            logger.info(f"Generated image list content: {image_list_content}")

            logger.info("Editing image list content")
            edited_content = await edit_image_list_content(image_list_content)
            logger.info(f"Edited image list content: {edited_content}")

            try:
                logger.info("Generating image")
                image = generate_image_list(
                    edited_content,
                    save_locally=os.getenv("ENVIRONMENT") == "development",
                )
                logger.info("Image generated successfully")

                logger.info("Uploading image to Supabase")
                file_name = f"image_list_{post_id}.png"
                image_url = upload_to_supabase(supabase, image, "images", file_name)
                logger.info(f"Image uploaded successfully. URL: {image_url}")

                generated_content = {
                    "provider": "twitter",
                    "type": "image_list",
                    "content": edited_content,
                    "image_url": image_url,
                    "thumbnail_url": content_data.get("thumbnail_url"),
                }
                return True, "Content generated successfully", generated_content
            except Exception as e:
                logger.error(f"Error in image generation or upload: {str(e)}")
                return False, f"Error in image generation or upload: {str(e)}", {}

        elif content_type == "precta_tweet":
            precta_tweets = await generate_precta_tweet(
                original_content, account_profile
            )
            edited_tweets = await edit_content(precta_tweets, "pre-CTA tweet")
            edited_tweets[1]["text"] = format_tweet_with_link(
                edited_tweets[1]["text"], account_profile.subscribe_url
            )
            generated_content = {
                "provider": "twitter",
                "type": "precta_tweet",
                "content": edited_tweets,
                "thumbnail_url": content_data.get("thumbnail_url"),  # Add this line
            }

        elif content_type == "postcta_tweet":
            postcta_tweets = await generate_postcta_tweet(
                original_content, account_profile, web_url
            )
            edited_tweets = await edit_content(postcta_tweets, "post-CTA tweet")
            edited_tweets[1]["text"] = format_tweet_with_link(
                edited_tweets[1]["text"], web_url
            )
            generated_content = {
                "provider": "twitter",
                "type": "postcta_tweet",
                "content": edited_tweets,
                "thumbnail_url": content_data.get("thumbnail_url"),
            }

        elif content_type == "thread_tweet":
            thread_tweets = await generate_thread_tweet(
                original_content, web_url, account_profile
            )
            edited_tweets = await edit_content(thread_tweets, "thread tweet")
            edited_tweets[-1]["text"] = format_tweet_with_link(
                edited_tweets[1]["text"], account_profile.subscribe_url
            )
            generated_content = {
                "provider": "twitter",
                "type": "thread_tweet",
                "content": edited_tweets,
                "thumbnail_url": content_data.get("thumbnail_url"),
            }

        elif content_type == "long_form_tweet":
            long_form_tweet = await generate_long_form_tweet(
                original_content, account_profile
            )
            edited_tweet = await edit_content(
                [{"type": "long_post", "text": long_form_tweet}], "long-form tweet"
            )
            generated_content = {
                "provider": "twitter",
                "type": "long_form_tweet",
                "content": edited_tweet,
                "thumbnail_url": content_data.get("thumbnail_url"),
            }

        elif content_type == "linkedin":
            linkedin_post = await generate_linkedin_post(
                original_content, account_profile
            )
            edited_post = await edit_content(
                [{"type": "post", "text": linkedin_post}], "LinkedIn post"
            )
            generated_content = {
                "provider": "linkedin",
                "type": "linkedin_post",
                "content": edited_post,
                "thumbnail_url": content_data.get("thumbnail_url"),
            }

        logger.info(f"Content generation and editing completed for {content_type}")
        return (
            True,
            f"Content generated and edited successfully for {content_type}",
            generated_content,
        )

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
