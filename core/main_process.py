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
        # Step 1: Fetch the content from the newsletter source
        content_data = await fetch_beehiiv_content(account_profile, post_id, supabase)
        original_content = content_data.get("free_content")
        web_url = content_data.get("web_url")
        thumbnail_url = content_data.get("thumbnail_url")

        if not original_content:
            logger.error(f"No content found for post ID: {post_id}")
            return {"error": "No content found", "success": False}

        # Step 2: Analyze the structure of the content
        newsletter_structure: str = await analyze_structure(original_content)

        # Step 3: Determine the content strategy
        content_strategy: str = await determine_content_strategy(newsletter_structure)

        logger.debug(f"Raw content_strategy: {content_strategy}")

        try:
            strategy_list = json.loads(content_strategy)
            if not isinstance(strategy_list, list):
                logger.error(f"Parsed content strategy is not a list: {strategy_list}")
                return {"error": "Content strategy is not a list", "success": False}
            logger.info(f"Parsed strategy list: {strategy_list}")
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse content strategy JSON: {e.msg} at line {e.lineno} column {e.colno} (char {e.pos})"
            )
            return {"error": "Failed to parse content strategy", "success": False}

        # Step 5: Process each section independently for content generation
        generated_contents: List[dict] = []
        for strategy in strategy_list:
            post_number = strategy.get("post_number", "unknown")
            logger.info(f"Processing section for post number: {post_number}")

            try:
                # Step 6: Generate content for this section
                generated_content = await generate_content(
                    strategy, content_type, account_profile, web_url, post_number
                )
                logger.info(
                    f"Generated content for post {post_number}: {generated_content}"
                )

                if (
                    not generated_content
                    or "content_container" not in generated_content
                ):
                    logger.error(
                        f"'content_container' missing or invalid for post {post_number}: {generated_content}"
                    )
                    continue

                # Add the generated section content to the result list
                generated_contents.append(
                    {
                        "post_number": post_number,
                        "post_content": generated_content["content_container"],
                    }
                )

            except Exception as e:
                logger.error(
                    f"Error generating content for post {post_number}: {str(e)}"
                )
                continue  # Continue to next section instead of breaking

        # Step 8: Fallback to the entire content if no valid content was generated
        if not generated_contents:
            logger.warning(
                "No valid content generated, falling back to full newsletter content."
            )
            try:
                fallback_content = await generate_content(
                    {
                        "post_number": "1",
                        "section_title": "Full Newsletter",
                        "section_content": newsletter_structure,
                    },
                    content_type,
                    account_profile,
                    web_url,
                    "1",
                )
                logger.info(f"Fallback content generated: {fallback_content}")

                if not fallback_content or "content_container" not in fallback_content:
                    logger.error(
                        "Fallback content generation failed, 'content_container' missing"
                    )
                    return {
                        "error": "Failed to generate any valid content",
                        "success": False,
                    }

                generated_contents = [
                    {
                        "post_number": "1",
                        "post_content": fallback_content["content_container"],
                    }
                ]
            except Exception as e:
                logger.error(f"Error generating fallback content: {str(e)}")
                return {
                    "error": "Failed to generate fallback content",
                    "success": False,
                }

        # Step 9: Construct the final payload
        final_content = {
            "provider": "twitter" if "tweet" in content_type else "linkedin",
            "type": content_type,
            "content": generated_contents,  # List of all generated sections or fallback content
            "thumbnail_url": thumbnail_url,
            "metadata": {"web_url": web_url, "post_id": post_id},
            "success": True,
        }
        logger.info(f"Final content payload constructed: {final_content}")
        return final_content

    except Exception as e:
        logger.error(f"Error in run_main_process: {str(e)}")
        return {"error": str(e), "success": False}
