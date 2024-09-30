import logging
from typing import Any, Dict, Tuple
import os
import supabase
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.content.improved_llm_flow.content_editor import edit_content
from core.llm_steps.content_generator import generate_content
from core.models.content import Content, Post, ContentSegment
from core.content.content_type_loader import get_instructions_for_content_type

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    post_id: str,
    content_type: str,
    supabase: supabase.Client,
) -> Tuple[bool, str, Dict[str, Any]]:
    logger.info(
        f"Starting main process for post_id: {post_id}, content_type: {content_type}"
    )
    try:
        logger.info("Fetching content from Beehiiv")
        content_data = await fetch_beehiiv_content(account_profile, post_id, supabase)
        original_content = content_data.get("free_content")
        web_url = content_data.get("web_url")

        if not original_content or not web_url:
            logger.error("Failed to fetch content or web URL from Beehiiv")
            return False, "Failed to fetch content or web URL from Beehiiv", {}

        logger.info("Creating initial Content object")
        initial_content = Content(
            posts=[
                Post(
                    post_number=1,
                    segments=[
                        ContentSegment(type="main_content", content=original_content)
                    ],
                )
            ],
            original_content=original_content,
            content_type=content_type,
            account_id=account_profile.account_id,
            metadata={"web_url": web_url, "post_id": post_id},
        )

        logger.info(f"Getting instructions for content type: {content_type}")
        instructions = get_instructions_for_content_type(content_type)
        logger.debug(f"Instructions: {instructions}")

        logger.info("Generating content")
        generated_content = await generate_content(
            initial_content,
            instructions,
            account_profile,
            supabase,
            save_locally=os.getenv("ENVIRONMENT") == "development",
        )
        logger.debug(f"Generated content: {generated_content}")

        if content_type != "image_list":
            logger.info("Editing content")
            edited_content = await edit_content(generated_content, content_type)
            logger.debug(f"Edited content: {edited_content}")
        else:
            logger.info("Extracting content for image_list")
            edited_content = next(
                (
                    seg.content
                    for seg in generated_content.posts[0].segments
                    if seg.type == "content"
                ),
                None,
            )
            logger.debug(f"Extracted content: {edited_content}")

        logger.info("Preparing result")
        result = {
            "provider": (
                "twitter"
                if content_type.endswith("tweet") or content_type == "image_list"
                else "linkedin"
            ),
            "type": content_type,
            "content": edited_content,
            "thumbnail_url": content_data.get("thumbnail_url"),
        }

        if content_type == "image_list":
            image_url = next(
                (
                    seg.content
                    for seg in generated_content.posts[0].segments
                    if seg.type == "image_url"
                ),
                None,
            )
            if image_url:
                result["image_url"] = image_url
                logger.info(f"Image URL added to result: {image_url}")

        logger.info("Main process completed successfully")
        return True, "Content generated and edited successfully", result

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
