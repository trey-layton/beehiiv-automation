import json
import logging
import re
from typing import Dict, Any, List, Optional
from supabase import Client as SupabaseClient

from core.content.beehiiv_handler import (
    fetch_beehiiv_content,
    transform_images_into_placeholders,
)
from core.models.account_profile import AccountProfile
from core.llm_steps.structure_analysis import analyze_structure
from core.llm_steps.content_strategy import determine_content_strategy
from core.llm_steps.content_generator import generate_content
from core.llm_steps.content_personalization import (
    personalize_content,
    get_instructions_for_content_type,
)
from core.llm_steps.hook_writer import write_hooks
from core.llm_steps.ai_polisher import ai_polish
from core.llm_steps.image_relevance import check_image_relevance
from core.services.status_updates import StatusService

# Import the CarouselGenerator for creating carousels
from core.content.image_generation.carousel_generator import CarouselGenerator

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    content_id: str,
    post_id: Optional[str],
    content_type: str,
    supabase: SupabaseClient,
    content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point for generating all PostOnce content. It:
    1. Fetches the Beehiiv content (or uses pasted content).
    2. Analyzes structure.
    3. Determines strategy (sections).
    4. For each section, calls the chain of LLM steps:
       - generate_content
       - check_image_relevance
       - personalize_content
       - hook_writer (unless carousel)
       - ai_polish
    5. If carousel type, generate images/PDF and structure them properly in the final schema.
    6. Returns the final dictionary with the shape the frontend expects.
    """
    status_service = StatusService(supabase)

    try:
        # Step 1: Fetch or set content
        await status_service.update_status(content_id, "analyzing")
        if post_id:
            try:
                content_data = await fetch_beehiiv_content(
                    account_profile, post_id, supabase
                )
                original_content = content_data.get("free_content", "")
                web_url = content_data.get("web_url")
                thumbnail_url = content_data.get("thumbnail_url")
            except Exception as e:
                logger.error(f"Error fetching Beehiiv content: {str(e)}")
                await status_service.update_status(content_id, "failed")
                return {"error": "Failed to fetch content", "success": False}
        else:
            original_content = content
            web_url = None
            thumbnail_url = None
            post_id = "pasted-content"

        # Safely transform images in HTML to placeholders for the LLM
        if original_content:
            original_content = transform_images_into_placeholders(original_content)
        else:
            await status_service.update_status(content_id, "failed")
            return {"error": "No content found", "success": False}

        # Step 2: Analyze structure
        await status_service.update_status(content_id, "analyzing_structure")
        newsletter_structure: str = await analyze_structure(original_content)

        # Step 3: Determine strategy
        await status_service.update_status(content_id, "determining_strategy")
        content_strategy: str = await determine_content_strategy(newsletter_structure)

        try:
            strategy_list = json.loads(content_strategy)
            if not isinstance(strategy_list, list):
                await status_service.update_status(content_id, "failed")
                return {"error": "Content strategy is not a list", "success": False}
        except json.JSONDecodeError:
            await status_service.update_status(content_id, "failed")
            return {"error": "Failed to parse content strategy", "success": False}

        content_type_instructions = get_instructions_for_content_type(content_type)
        generated_contents: List[dict] = []

        # Step 4: Generation and post-processing loop
        await status_service.update_status(content_id, "generating")
        for strategy in strategy_list:
            post_number = strategy.get("post_number", "unknown")

            try:
                # -- 4a: Cleanup section for generation (image placeholders, etc.) --
                section_content = strategy.get("section_content", "")
                image_pattern = r"\[image:(.*?)\]"
                image_urls = [
                    match.group(1)
                    for match in re.finditer(image_pattern, section_content)
                ]
                logger.info(f"Found {len(image_urls)} images in content: {image_urls}")

                # Remove "[image:...]" placeholders from LLM input
                cleaned_section_content = re.sub(image_pattern, "", section_content)
                strategy["section_content"] = cleaned_section_content

                # -- 4b: Generate initial content from LLM --
                generated_content = await generate_content(
                    strategy,
                    content_type,
                    account_profile,
                    web_url,
                    post_number,
                )
                if (
                    not generated_content
                    or "content_container" not in generated_content
                ):
                    logger.warning(f"No valid content for post {post_number}")
                    continue

                # -- 4c: Check image relevance (only if we found placeholders) --
                if image_urls:
                    logger.info("Running image relevance check before personalization.")
                    updated_generated_content = await check_image_relevance(
                        generated_content, image_urls, account_profile, content_type
                    )
                    if (
                        updated_generated_content
                        and "content_container" in updated_generated_content
                    ):
                        generated_content = updated_generated_content

                # -- 4d: Personalize the content --
                personalized_content = await personalize_content(
                    generated_content,
                    account_profile,
                    content_type,
                    content_type_instructions,
                )
                content_to_use = personalized_content.get(
                    "content_container", generated_content["content_container"]
                )

                # -- 4e: Add hooks if not a carousel type --
                await status_service.update_status(content_id, "writing_hooks")
                if content_type not in ["carousel_tweet", "carousel_post"]:
                    content_with_hooks = await write_hooks(
                        {
                            "post_number": post_number,
                            "content_container": content_to_use,
                        },
                        account_profile,
                        content_type,
                        content_type_instructions,
                    )
                    content_for_polish = content_with_hooks.get(
                        "content_container", content_to_use
                    )
                else:
                    content_for_polish = content_to_use

                # -- 4f: Polish the content with AI --
                await status_service.update_status(content_id, "polishing")
                polished_content = await ai_polish(
                    {
                        "post_number": post_number,
                        "content_container": content_for_polish,
                    },
                    account_profile,
                    content_type,
                    content_type_instructions,
                )
                final_content_to_use = polished_content.get(
                    "content_container", content_for_polish
                )

                # -- 4g: If this is a carousel, generate images/PDF and shape data properly --
                if content_type in ["carousel_tweet", "carousel_post"]:
                    platform = (
                        "linkedin" if content_type == "carousel_post" else "twitter"
                    )
                    carousel_generator = CarouselGenerator(platform)
                    try:
                        # Generate the actual carousel images or PDF
                        await status_service.update_status(content_id, "generating")
                        image_urls = await carousel_generator.generate_carousel(
                            {
                                "post_number": post_number,
                                "content_container": final_content_to_use,
                            },
                            supabase,
                        )
                        if not image_urls:
                            raise ValueError("Failed to generate carousel images")

                        # For the final shape:
                        # - LinkedIn expects a single PDF URL, so set `carousel_pdf_url`.
                        # - Twitter expects multiple slide URLs, so set `carousel_urls`.

                        if content_type == "carousel_post":
                            # For LinkedIn
                            generated_contents.append(
                                {
                                    "post_number": int(post_number),
                                    "post_content": [
                                        {
                                            "post_type": "carousel_post",
                                            "post_content": "",  # Optionally set a short caption
                                            "carousel_pdf_url": image_urls[0],
                                        }
                                    ],
                                }
                            )
                        else:
                            # For Twitter
                            generated_contents.append(
                                {
                                    "post_number": int(post_number),
                                    "post_content": [
                                        {
                                            "post_type": "carousel_tweet",
                                            "post_content": "",  # Optionally set a short caption
                                            "carousel_urls": image_urls,
                                        }
                                    ],
                                }
                            )

                    except Exception as e:
                        logger.error(
                            f"Carousel generation failed for {post_number}: {e}"
                        )
                        await status_service.update_status(content_id, "failed")
                        return {"error": str(e), "success": False}

                else:
                    # -- 4h: Otherwise, just store the final content in the usual structure --
                    generated_contents.append(
                        {
                            "post_number": int(post_number),
                            "post_content": final_content_to_use,
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing post {post_number}: {str(e)}")
                continue

        # If we ended up with nothing, fail out
        if not generated_contents:
            await status_service.update_status(content_id, "failed")
            return {"error": "Failed to generate any valid content", "success": False}

        # Step 5: Build final response
        final_content = {
            "provider": "twitter" if "tweet" in content_type else "linkedin",
            "type": content_type,
            "content": generated_contents,
            "thumbnail_url": thumbnail_url or "",
            "metadata": {"web_url": web_url or "", "post_id": post_id},
            "success": True,
        }

        await status_service.update_status(content_id, "generated")
        return final_content

    except Exception as e:
        logger.error(f"Fatal error in run_main_process: {str(e)}")
        await status_service.update_status(content_id, "failed")
        return {"error": str(e), "success": False}
