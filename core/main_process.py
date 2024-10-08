import json
import logging
from typing import Dict, Any, List
from supabase import Client as SupabaseClient
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.llm_steps.structure_analysis import analyze_structure
from core.llm_steps.content_strategy import determine_content_strategy
from core.llm_steps.content_generator import generate_content

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    post_id: str,
    content_type: str,
    supabase: SupabaseClient,
) -> Dict[str, Any]:
    try:
        # Step 1: Fetch the content from the newsletter source (beehiiv)
        content_data = await fetch_beehiiv_content(account_profile, post_id, supabase)
        original_content = content_data.get("free_content")
        web_url = content_data.get("web_url")
        thumbnail_url = content_data.get("thumbnail_url")

        # Step 2: Analyze the structure of the content
        newsletter_structure: str = await analyze_structure(original_content)

        # Step 3: Determine the content strategy based on the structure
        content_strategy: str = await determine_content_strategy(newsletter_structure)

        # Step 4: Parse the content strategy (ensure it's valid JSON directly from the LLM output)
        try:
            strategy_list = json.loads(content_strategy)  # Ensure it's parsed as JSON
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse content strategy JSON: {str(e)}")
            return {"error": "Failed to parse content strategy", "success": False}

        # Step 5: Process each section of the content strategy as its own independent entity
        generated_contents: List[Dict[str, Any]] = []
        for strategy in strategy_list:
            post_number = strategy.get(
                "post_number", "unknown"
            )  # Retrieve post number from strategy
            section_title = strategy.get("section_title", "unknown")

            try:
                post_content = await generate_content(
                    strategy,
                    content_type,
                    account_profile,
                    web_url,
                    post_number,  # Pass the post_number to generate_content
                )

                if isinstance(post_content, dict) and "content" in post_content:
                    generated_contents.append(post_content)
                else:
                    logger.error(f"Invalid post content format for post {post_number}")
                    return {"error": "Invalid post content format", "success": False}

            except Exception as e:
                logger.error(
                    f"Error generating content for post {post_number}: {str(e)}"
                )
                return {"error": str(e), "success": False}

        final_content = {
            "provider": "twitter" if "tweet" in content_type else "linkedin",
            "type": content_type,
            "content": generated_contents,
            "thumbnail_url": thumbnail_url,
            "metadata": {"web_url": web_url, "post_id": post_id},
        }
        logger.info(final_content)
        return final_content

    except Exception as e:
        logger.error(f"Error in run_main_process for post_id {post_id}: {str(e)}")
        return {
            "error": str(e),
            "success": False,
        }
