import logging
from typing import Any, Dict, Tuple
import os
import supabase
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.content.improved_llm_flow.content_editor import edit_content
from core.llm_steps.content_generator import generate_content

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    post_id: str,
    content_type: str,
    supabase: supabase.Client,
) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        content_data = await fetch_beehiiv_content(account_profile, post_id, supabase)
        original_content = content_data.get("free_content")
        web_url = content_data.get("web_url")

        if not original_content or not web_url:
            logger.error("Failed to fetch content or web URL from Beehiiv")
            return False, "Failed to fetch content or web URL from Beehiiv", {}

        generated_content = await generate_content(
            content_type,
            original_content,
            account_profile,
            supabase,
            web_url=web_url,
            post_id=post_id,
            save_locally=os.getenv("ENVIRONMENT") == "development",
        )

        if content_type != "image_list":
            edited_content = await edit_content(generated_content, content_type)
        else:
            edited_content = generated_content["content"]

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
            result["image_url"] = generated_content["image_url"]

        return True, "Content generated and edited successfully", result

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
