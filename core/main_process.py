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
from core.services.status_updates import StatusService
from core.content.image_generation.carousel_generator import CarouselGenerator
from core.llm_steps.image_relevance import check_image_relevance  # Add this import

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    content_id: str,
    post_id: Optional[str],
    content_type: str,
    supabase: SupabaseClient,
    content: Optional[str] = None,
) -> Dict[str, Any]:
    status_service = StatusService(supabase)

    try:
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

        if original_content:
            original_content = transform_images_into_placeholders(original_content)

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
        carousel_images: List[str] = []

        # Step 4: Generation and processing loop
        await status_service.update_status(content_id, "generating")
        for strategy in strategy_list:
            post_number = strategy.get("post_number", "unknown")
            try:
                section_content = strategy.get("section_content", "")
                image_pattern = r"\[image:(.*?)\]"
                image_urls = [
                    match.group(1)
                    for match in re.finditer(image_pattern, section_content)
                ]
                logger.info(image_urls)

                # Remove image placeholders from section_content before content generation
                cleaned_section_content = re.sub(image_pattern, "", section_content)
                strategy["section_content"] = cleaned_section_content

                # Generate content
                generated_content = await generate_content(
                    strategy, content_type, account_profile, web_url, post_number
                )
                if (
                    not generated_content
                    or "content_container" not in generated_content
                ):
                    continue

                # Check image relevance if we have image URLs
                if image_urls:
                    logger.info(
                        f"Before image relevance, generated_content: {json.dumps(generated_content, indent=2)}"
                    )
                    updated_generated_content = await check_image_relevance(
                        generated_content, image_urls, account_profile, content_type
                    )
                    logger.info(
                        f"After image relevance, updated_generated_content: {json.dumps(updated_generated_content, indent=2)}"
                    )
                    if (
                        updated_generated_content
                        and "content_container" in updated_generated_content
                    ):
                        generated_content = updated_generated_content
                        logger.info(
                            f"After assignment, generated_content: {json.dumps(generated_content, indent=2)}"
                        )

                # Now personalize using the updated generated_content
                personalized_content = await personalize_content(
                    generated_content,
                    account_profile,
                    content_type,
                    content_type_instructions,
                )

                content_to_use = personalized_content.get(
                    "content_container", generated_content["content_container"]
                )

                # Step 6: Hooks (skip for carousel types)
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

                # Step 7: Polish
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

                # Step 8: Generate carousel images if needed
                if content_type in ["carousel_tweet", "carousel_post"]:
                    platform = (
                        "linkedin" if content_type == "carousel_post" else "twitter"
                    )
                    carousel_generator = CarouselGenerator(platform)

                    try:
                        await status_service.update_status(content_id, "generating")
                        image_urls = await carousel_generator.generate_carousel(
                            {
                                "post_number": post_number,
                                "content_container": final_content_to_use,
                            },
                            supabase,
                        )
                        if not image_urls:
                            raise Exception("Failed to generate carousel images")
                        carousel_images.extend(image_urls)

                        # Add the carousel content with appropriate post_type
                        post_type = (
                            "main_post"
                            if content_type == "carousel_post"
                            else "main_tweet"
                        )

                        if content_type == "carousel_post":
                            # For LinkedIn, use carousel_pdf_url
                            generated_contents.append(
                                {
                                    "post_number": int(post_number),
                                    "post_content": [
                                        {
                                            "post_type": post_type,
                                            "post_content": "",
                                            "carousel_pdf_url": image_urls[
                                                0
                                            ],  # LinkedIn expects single PDF
                                        }
                                    ],
                                }
                            )
                        else:
                            # For Twitter, use carousel_urls array
                            carousel_images.extend(image_urls)
                            generated_contents.append(
                                {
                                    "post_number": int(post_number),
                                    "post_content": [
                                        {
                                            "post_type": post_type,
                                            "post_content": "",
                                            "carousel_urls": image_urls,
                                        }
                                    ],
                                }
                            )

                    except Exception as e:
                        logger.error(f"Carousel generation failed: {str(e)}")
                        await status_service.update_status(content_id, "failed")
                        return {"error": str(e), "success": False}

                else:
                    # Handle non-carousel content types
                    generated_contents.append(
                        {
                            "post_number": int(post_number),
                            "post_content": final_content_to_use,
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing post {post_number}: {str(e)}")
                continue

        if not generated_contents:
            await status_service.update_status(content_id, "failed")
            return {"error": "Failed to generate any valid content", "success": False}

        # Build final response
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
        await status_service.update_status(content_id, "failed")
        return {"error": str(e), "success": False}
