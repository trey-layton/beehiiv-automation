import logging
from typing import Any, Dict, Tuple
from core.content.content_fetcher import fetch_beehiiv_content
<<<<<<< Updated upstream
from core.social_media.twitter.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweet,
    generate_long_form_tweet,
)
from core.social_media.linkedin.generate_linkedin_post import generate_linkedin_post
from core.config.user_config import load_user_config
from core.content.improved_llm_flow.classifier import classify_and_summarize
from core.content.improved_llm_flow.content_improver import improve_content
from core.content.improved_llm_flow.cta_adder import add_cta

=======
from core.models.account_profile import AccountProfile
from core.content.improved_llm_flow.content_editor import edit_content
>>>>>>> Stashed changes

logger = logging.getLogger(__name__)


async def run_main_process(
    user_config: Dict[str, Any],
    edition_url: str,
    precta_tweet: bool = False,
    postcta_tweet: bool = False,
    thread_tweet: bool = False,
    long_form_tweet: bool = False,
    linkedin: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    logger.info(f"run_main_process started for user {user_config['id']}")
    generated_content = {}

    try:
        content_data = await fetch_beehiiv_content(user_config, edition_url)
        original_content = content_data.get("free_content")

        if not original_content:
            logger.error("Failed to fetch content from Beehiiv")
            return False, "Failed to fetch content from Beehiiv", {}

        classification_result = await classify_and_summarize(original_content)
        classification = classification_result.get("classification", "Unknown")
        logger.info(f"Content classified as: {classification}")

        if precta_tweet:
            logger.info("Generating pre-CTA tweet")
            precta_content = await generate_precta_tweet(
                original_content, user_config, classification
            )
<<<<<<< Updated upstream
            if precta_content:
                improved_precta = await improve_content(precta_content, "single_tweet")
                cta_added_precta = await add_cta(
                    improved_precta, "precta_tweet", user_config, edition_url
                )
                generated_content["precta_tweet"] = [
                    {"text": improved_precta},
                    {"text": cta_added_precta},
                ]
=======
            edited_tweet = await edit_content(precta_tweet, "pre-CTA tweet")
            generated_content = {
                "provider": "twitter",
                "type": "precta_tweet",
                "content": [{"type": "post", "text": edited_tweet}],
            }
>>>>>>> Stashed changes

        if postcta_tweet:
            logger.info("Generating post-CTA tweet")
            postcta_content = await generate_postcta_tweet(
                original_content, user_config, classification
            )
<<<<<<< Updated upstream
            if postcta_content:
                improved_postcta = await improve_content(
                    postcta_content, "single_tweet"
                )
                cta_added_postcta = await add_cta(
                    improved_postcta, "postcta_tweet", user_config, edition_url
                )
                generated_content["postcta_tweet"] = [
                    {"text": improved_postcta},
                    {"text": cta_added_postcta},
                ]
=======
            edited_tweet = await edit_content(postcta_tweet, "post-CTA tweet")
            generated_content = {
                "provider": "twitter",
                "type": "postcta_tweet",
                "content": [{"type": "post", "text": edited_tweet}],
            }
>>>>>>> Stashed changes

        if thread_tweet:
            logger.info("Generating thread tweet")
            thread_content = await generate_thread_tweet(
                original_content,
                content_data.get("web_url"),
                user_config,
                classification,
            )
<<<<<<< Updated upstream
            if thread_content:
                improved_thread = await improve_content(thread_content, "thread")
                cta_added_thread = await add_cta(
                    improved_thread, "thread_tweet", user_config, edition_url
                )
                generated_content["thread_tweet"] = improved_thread + [
                    {"text": cta_added_thread}
                ]
=======
            edited_thread = []
            for tweet in thread_tweet:
                edited_tweet = await edit_content(tweet["text"], "thread tweet")
                edited_thread.append({"type": tweet["type"], "text": edited_tweet})
            generated_content = {
                "provider": "twitter",
                "type": "thread_tweet",
                "content": edited_thread,
            }
>>>>>>> Stashed changes

        if long_form_tweet:
            logger.info("Generating long-form tweet")
            long_form_content = await generate_long_form_tweet(
                original_content, user_config, classification
            )
            if long_form_content:
                improved_long_form = await improve_content(
                    long_form_content, "long_form_tweet"
                )
                cta_added_long_form = await add_cta(
                    improved_long_form, "long_form_tweet", user_config, edition_url
                )
                generated_content["long_form_tweet"] = [
                    {"text": improved_long_form},
                    {"text": cta_added_long_form},
                ]

        if linkedin:
            logger.info("Generating LinkedIn post")
            linkedin_content = await generate_linkedin_post(
                original_content, user_config, classification
            )
<<<<<<< Updated upstream
            if linkedin_content:
                improved_linkedin = await improve_content(
                    linkedin_content, "linkedin_post"
                )
                generated_content["linkedin"] = [{"text": improved_linkedin}]

        logger.info(
            f"Content generation completed. Generated types: {list(generated_content.keys())}"
        )
        return True, "Content generated successfully", generated_content
=======
            edited_tweet = await edit_content(long_form_tweet, "long-form tweet")
            generated_content = {
                "provider": "twitter",
                "type": "long_form_tweet",
                "content": [{"type": "long_post", "text": edited_tweet}],
            }

        elif content_type == "linkedin":
            from core.social_media.linkedin.generate_linkedin_post import (
                generate_linkedin_post,
            )

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
>>>>>>> Stashed changes

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", generated_content
