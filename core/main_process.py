import logging
from typing import Any, Dict, Tuple
import os
from supabase import Client as SupabaseClient
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.content.improved_llm_flow.content_editor import edit_content
from core.llm_steps.content_generator import generate_content
from core.models.content import Content, Post, ContentSegment, ContentStrategy
from core.content.content_type_loader import get_instructions_for_content_type
from core.llm_steps.structure_analysis import analyze_structure
from core.llm_steps.content_strategy import determine_content_strategy

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    post_id: str,
    content_type: str,
    supabase: SupabaseClient,
) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        content_data = await fetch_beehiiv_content(account_profile, post_id, supabase)
        original_content = content_data.get("free_content")
        web_url = content_data.get("web_url")

        content_segments = await analyze_structure(content_data["free_content"])
        content_strategy = await determine_content_strategy(content_segments)

        generated_posts = []
        for strategy in content_strategy:
            initial_content = Content(
                segments=[
                    ContentSegment(type=strategy.section_type, content=strategy.content)
                ],
                strategy=[strategy],
                posts=[],
                original_content=original_content,
                content_type=content_type,
                account_id=account_profile.account_id,
                metadata={"web_url": web_url, "post_id": post_id},
            )

            instructions = get_instructions_for_content_type(content_type)

            generated_content = await generate_content(
                initial_content,
                instructions,
                account_profile,
                supabase,
                save_locally=os.getenv("ENVIRONMENT") == "development",
            )

            if content_type != "image_list":
                edited_content = await edit_content(generated_content, content_type)
            else:
                edited_content = generated_content

            generated_posts.extend(edited_content.posts)

        result = {
            "provider": (
                "twitter"
                if content_type.endswith("tweet") or content_type == "image_list"
                else "linkedin"
            ),
            "type": content_type,
            "posts": [
                {
                    "post_number": post.post_number,
                    "section_type": post.section_type,
                    "content": post.content,
                    "metadata": post.metadata,
                }
                for post in generated_posts
            ],
            "thumbnail_url": content_data.get("thumbnail_url"),
            "original_content": original_content,
            "content_type": content_type,
            "account_id": account_profile.account_id,
            "metadata": {"web_url": web_url, "post_id": post_id},
        }

        if content_type == "image_list" and generated_posts:
            image_url = generated_posts[0].metadata.get("image_url")
            if image_url:
                result["image_url"] = image_url

        return True, "Content generated and edited successfully", result

    except Exception as e:
        logger.exception(f"Error in run_main_process: {str(e)}")
        return False, f"An unexpected error occurred: {str(e)}", {}
