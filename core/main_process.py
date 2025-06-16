"""
Main Content Processing Pipeline for PostOnce Backend.

This module orchestrates the complete AI-powered content transformation pipeline,
converting newsletter content into optimized social media posts through a
sophisticated 7-step process:

1. **Content Fetching**: Retrieve newsletter content from Beehiiv API or direct input
2. **Structure Analysis**: AI analyzes content structure and identifies logical sections
3. **Strategy Determination**: AI determines optimal posting strategy per section
4. **Content Generation**: Generate initial platform-specific content variations
5. **Image Relevance**: Check and incorporate relevant images with content
6. **Content Personalization**: Apply user's unique brand voice and writing style
7. **Hook Writing & Polishing**: Add engaging hooks, CTAs, and final optimization

Each step feeds into the next, building from raw newsletter content to polished,
platform-optimized social media posts that maintain the user's authentic voice
while maximizing engagement potential.

Key Features:
- Real-time status updates via StatusService
- Robust error handling with graceful degradation
- Image placeholder processing and relevance checking
- Platform-specific content formatting (Twitter/LinkedIn)
- Brand voice preservation through personalization
- Comprehensive logging for debugging and monitoring
- Carousel generation for visual content types

Usage:
    result = await run_main_process(
        account_profile=account_profile,
        content_id="unique_content_id",
        post_id="beehiiv_post_id",  # OR content="direct_content"
        content_type="thread_tweet",
        supabase=supabase_client
    )
"""

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

# Import the CarouselGenerator for creating carousels.
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
    Execute the complete AI-powered content generation pipeline.

    This function orchestrates the transformation of newsletter content into
    optimized social media posts through a 7-step AI processing pipeline.
    Each step is tracked with real-time status updates and comprehensive
    error handling.

    Args:
        account_profile: User account profile containing API keys, preferences,
                        and examples for voice/style matching
        content_id: Unique identifier for this content generation process,
                   used for status tracking and logging
        post_id: Optional Beehiiv post ID to fetch content from API.
                Mutually exclusive with 'content' parameter
        content_type: Type of social media content to generate:
                     - precta_tweet: Pre-newsletter announcement
                     - postcta_tweet: Post-newsletter CTA
                     - thread_tweet: Multi-tweet thread
                     - long_form_tweet: Extended tweet content
                     - long_form_post: LinkedIn long-form post
                     - carousel_tweet: Twitter visual carousel (4 slides max)
                     - carousel_post: LinkedIn PDF carousel (8 slides max)
        supabase: Supabase client for database operations and file storage
        content: Optional direct content input as string.
                Mutually exclusive with 'post_id' parameter

    Returns:
        Dict containing the generated content and metadata:
        {
            "provider": "twitter|linkedin",
            "type": content_type,
            "content": [
                {
                    "post_number": 1,
                    "post_content": {...}  # Platform-specific structure
                }
            ],
            "thumbnail_url": "https://...",
            "metadata": {
                "web_url": "https://...",
                "post_id": "..."
            },
            "success": True
        }

        On error:
        {
            "error": "Error description",
            "success": False
        }

    Raises:
        Exception: Critical errors that prevent processing continuation

    Pipeline Steps:
        1. Content Fetching: Retrieve from Beehiiv API or use direct input
        2. Structure Analysis: AI identifies content sections and themes
        3. Strategy Generation: AI determines optimal content distribution
        4. Content Generation: Create platform-specific variations
        5. Image Processing: Handle image placeholders and relevance
        6. Personalization: Apply user's brand voice and writing style
        7. Hook Writing & Polish: Add engaging elements and final optimization

    Status Updates:
        The function provides real-time status updates via StatusService:
        - "analyzing": Initial content analysis
        - "analyzing_structure": Breaking down content sections
        - "determining_strategy": Planning content strategy
        - "generating": Creating social media content
        - "writing_hooks": Adding engaging hooks and CTAs
        - "polishing": Final optimization pass
        - "generated": Process completed successfully
        - "failed": Process failed with error

    Example:
        ```python
        result = await run_main_process(
            account_profile=user_profile,
            content_id="content_123",
            post_id="beehiiv_post_456",
            content_type="thread_tweet",
            supabase=supabase_client
        )

        if result["success"]:
            for post in result["content"]:
                print(f"Post {post['post_number']}: {post['post_content']}")
        else:
            print(f"Error: {result['error']}")
        ```
    """
    status_service = StatusService(supabase)

    try:
        # Step 1: Content Fetching and Preparation
        await status_service.update_status(content_id, "analyzing")
        if post_id:
            # Fetch content from Beehiiv API
            try:
                content_data = await fetch_beehiiv_content(
                    account_profile, post_id, supabase
                )
                original_content = content_data.get("free_content", "")
                web_url = content_data.get("web_url")
                thumbnail_url = content_data.get("thumbnail_url")
                logger.info(f"Successfully fetched Beehiiv content for post {post_id}")
            except Exception as e:
                logger.error(f"Error fetching Beehiiv content: {str(e)}")
                await status_service.update_status(content_id, "failed")
                return {"error": "Failed to fetch content", "success": False}
        else:
            # Use direct content input
            original_content = content
            web_url = None
            thumbnail_url = None
            post_id = "pasted-content"
            logger.info("Using direct content input for processing")

        # Safely transform images in HTML to placeholders for the LLM
        if original_content:
            original_content = transform_images_into_placeholders(original_content)
            logger.info("Transformed images to placeholders for AI processing")
        else:
            await status_service.update_status(content_id, "failed")
            return {"error": "No content found", "success": False}

        # Step 2: Structure Analysis
        await status_service.update_status(content_id, "analyzing_structure")
        logger.info("Starting structure analysis")
        newsletter_structure: str = await analyze_structure(original_content)
        logger.info("Completed structure analysis")

        # Step 3: Strategy Determination
        await status_service.update_status(content_id, "determining_strategy")
        logger.info("Starting content strategy determination")
        content_strategy: str = await determine_content_strategy(newsletter_structure)
        logger.info("Completed content strategy determination")

        # Validate strategy format
        try:
            strategy_list = json.loads(content_strategy)
            if not isinstance(strategy_list, list):
                await status_service.update_status(content_id, "failed")
                return {"error": "Content strategy is not a list", "success": False}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse content strategy: {content_strategy}")
            await status_service.update_status(content_id, "failed")
            return {"error": "Failed to parse content strategy", "success": False}

        # Get content type specific instructions
        content_type_instructions = get_instructions_for_content_type(content_type)
        generated_contents: List[dict] = []

        # Step 4-7: Process each strategy section through the pipeline
        await status_service.update_status(content_id, "generating")
        logger.info(f"Processing {len(strategy_list)} content sections")

        for i, strategy in enumerate(strategy_list):
            post_number = strategy.get("post_number", i + 1)
            logger.info(f"Processing section {post_number}")

            try:
                # -- 4a: Cleanup section for generation (image placeholders, etc.) --
                section_content = strategy.get("section_content", "")
                image_pattern = r"\[image:(.*?)\]"
                image_urls = [
                    match.group(1)
                    for match in re.finditer(image_pattern, section_content)
                ]
                logger.info(
                    f"Found {len(image_urls)} images in section {post_number}: {image_urls}"
                )

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
                    logger.warning(f"No valid content for section {post_number}")
                    continue

                # -- 4c: Check image relevance (only if we found placeholders) --
                if image_urls:
                    logger.info(
                        f"Running image relevance check for section {post_number}"
                    )
                    updated_generated_content = await check_image_relevance(
                        generated_content, image_urls, account_profile, content_type
                    )
                    if (
                        updated_generated_content
                        and "content_container" in updated_generated_content
                    ):
                        generated_content = updated_generated_content
                        logger.info(
                            f"Updated content with relevant images for section {post_number}"
                        )

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
                    # Add engaging hooks and CTAs
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
                        logger.info(f"Generating carousel for section {post_number}")
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

                        logger.info(
                            f"Successfully generated carousel for section {post_number}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Carousel generation failed for section {post_number}: {e}"
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

                logger.info(f"Successfully processed section {post_number}")

            except Exception as e:
                logger.error(f"Error processing section {post_number}: {str(e)}")
                continue

        # Validate final results
        if not generated_contents:
            await status_service.update_status(content_id, "failed")
            return {"error": "Failed to generate any valid content", "success": False}

        # Step 5: Build final response with platform detection
        provider = "twitter" if "tweet" in content_type else "linkedin"
        final_content = {
            "provider": provider,
            "type": content_type,
            "content": generated_contents,
            "thumbnail_url": thumbnail_url or "",
            "metadata": {"web_url": web_url or "", "post_id": post_id},
            "success": True,
        }

        await status_service.update_status(content_id, "generated")
        logger.info(f"Successfully completed processing for content_id: {content_id}")
        return final_content

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in main process: {str(e)}", exc_info=True)
        await status_service.update_status(content_id, "failed", error_message=str(e))
        return {"error": f"Processing failed: {str(e)}", "success": False}
