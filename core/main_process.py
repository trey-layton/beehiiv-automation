import json
import logging
from typing import Dict, Any, List, Optional
from supabase import Client as SupabaseClient
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.llm_steps.structure_analysis import analyze_structure
from core.llm_steps.content_strategy import determine_content_strategy
from core.llm_steps.content_generator import generate_content
from core.llm_steps.content_personalization import (
    personalize_content,
    get_instructions_for_content_type,
)
from core.llm_steps.hook_writer import write_hooks
from core.llm_steps.ai_polisher import ai_polish  # Add this import

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    post_id: Optional[str],
    content_type: str,
    supabase: SupabaseClient,
    content: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        # Step 1: Fetch the content from the newsletter source
        if post_id:
            content_data = await fetch_beehiiv_content(
                account_profile, post_id, supabase
            )
            original_content = content_data.get("free_content")
            web_url = content_data.get("web_url")
            thumbnail_url = content_data.get("thumbnail_url")
        else:
            original_content = content
            web_url = None
            thumbnail_url = None
            post_id = "pasted-content"

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

        # Get content type instructions once for all personalization
        content_type_instructions = get_instructions_for_content_type(content_type)

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

                # Step 7: Personalize the generated content
                try:
                    personalized_content = await personalize_content(
                        generated_content,
                        account_profile,
                        content_type,
                        content_type_instructions,
                    )
                    logger.info(
                        f"Personalized content for post {post_number}: {personalized_content}"
                    )

                    if (
                        not personalized_content
                        or "content_container" not in personalized_content
                    ):
                        logger.error(
                            f"Personalization failed for post {post_number}, using non-personalized content"
                        )
                        content_to_use = generated_content["content_container"]
                    else:
                        content_to_use = personalized_content["content_container"]

                    # Step 8: Generate hooks for the content
                    try:
                        content_with_hooks = await write_hooks(
                            {
                                "post_number": post_number,
                                "content_container": content_to_use,
                            },
                            account_profile,
                            content_type,
                            content_type_instructions,
                        )
                        logger.info(
                            f"Generated hooks for post {post_number}: {content_with_hooks}"
                        )

                        if (
                            not content_with_hooks
                            or "content_container" not in content_with_hooks
                        ):
                            logger.error(
                                f"Hook generation failed for post {post_number}, using content without hooks"
                            )
                            content_for_polish = content_to_use
                        else:
                            content_for_polish = content_with_hooks["content_container"]

                        # Step 9: Apply AI Polish
                        try:
                            polished_content = await ai_polish(
                                {
                                    "post_number": post_number,
                                    "content_container": content_for_polish,
                                },
                                account_profile,
                                content_type,
                                content_type_instructions,
                            )
                            logger.info(
                                f"Applied AI polish for post {post_number}: {polished_content}"
                            )

                            if (
                                not polished_content
                                or "content_container" not in polished_content
                            ):
                                logger.error(
                                    f"AI polish failed for post {post_number}, using unpolished content"
                                )
                                final_content_to_use = content_for_polish
                            else:
                                final_content_to_use = polished_content[
                                    "content_container"
                                ]

                        except Exception as e:
                            logger.error(
                                f"Error during AI polish for post {post_number}: {str(e)}"
                            )
                            final_content_to_use = content_for_polish

                    except Exception as e:
                        logger.error(
                            f"Error during hook generation for post {post_number}: {str(e)}"
                        )
                        final_content_to_use = content_to_use

                except Exception as e:
                    logger.error(
                        f"Error during personalization for post {post_number}: {str(e)}"
                    )
                    final_content_to_use = generated_content["content_container"]

                # Add the final content to the result list
                generated_contents.append(
                    {
                        "post_number": post_number,
                        "post_content": final_content_to_use,
                    }
                )

            except Exception as e:
                logger.error(
                    f"Error generating content for post {post_number}: {str(e)}"
                )
                continue

        # Fallback handling section - update to include AI polish in fallback flow
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

                # Process fallback content through the same pipeline
                try:
                    personalized_fallback = await personalize_content(
                        fallback_content,
                        account_profile,
                        content_type,
                        content_type_instructions,
                    )
                    if (
                        personalized_fallback
                        and "content_container" in personalized_fallback
                    ):
                        content_to_use = personalized_fallback["content_container"]
                    else:
                        content_to_use = fallback_content["content_container"]

                    # Add hook generation to fallback
                    try:
                        fallback_with_hooks = await write_hooks(
                            {"post_number": "1", "content_container": content_to_use},
                            account_profile,
                            content_type,
                            content_type_instructions,
                        )
                        if (
                            fallback_with_hooks
                            and "content_container" in fallback_with_hooks
                        ):
                            content_for_polish = fallback_with_hooks[
                                "content_container"
                            ]
                        else:
                            content_for_polish = content_to_use

                        # Add AI polish to fallback
                        try:
                            polished_fallback = await ai_polish(
                                {
                                    "post_number": "1",
                                    "content_container": content_for_polish,
                                },
                                account_profile,
                                content_type,
                                content_type_instructions,
                            )
                            if (
                                polished_fallback
                                and "content_container" in polished_fallback
                            ):
                                final_content_to_use = polished_fallback[
                                    "content_container"
                                ]
                            else:
                                final_content_to_use = content_for_polish
                        except Exception as e:
                            logger.error(f"Error polishing fallback content: {str(e)}")
                            final_content_to_use = content_for_polish
                    except Exception as e:
                        logger.error(
                            f"Error adding hooks to fallback content: {str(e)}"
                        )
                        final_content_to_use = content_to_use
                except Exception as e:
                    logger.error(f"Error personalizing fallback content: {str(e)}")
                    final_content_to_use = fallback_content["content_container"]

                generated_contents = [
                    {
                        "post_number": "1",
                        "post_content": final_content_to_use,
                    }
                ]
            except Exception as e:
                logger.error(f"Error generating fallback content: {str(e)}")
                return {
                    "error": "Failed to generate fallback content",
                    "success": False,
                }

        # Construct the final payload
        final_content = {
            "provider": "twitter" if "tweet" in content_type else "linkedin",
            "type": content_type,
            "content": generated_contents,
            "thumbnail_url": thumbnail_url,
            "metadata": {"web_url": web_url, "post_id": post_id},
            "success": True,
        }
        # Ensure thumbnail_url is a string
        if final_content["thumbnail_url"] is None:
            final_content["thumbnail_url"] = ""

        # Ensure metadata.web_url is a string
        if final_content["metadata"]["web_url"] is None:
            final_content["metadata"]["web_url"] = ""

        logger.info(f"Final content payload constructed: {final_content}")
        return final_content

    except Exception as e:
        logger.error(f"Error in run_main_process: {str(e)}")
        return {"error": str(e), "success": False}
