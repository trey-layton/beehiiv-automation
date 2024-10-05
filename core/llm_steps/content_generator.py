import logging
from typing import Dict, Any
from core.models.account_profile import AccountProfile
from core.models.content import Content, Post, ContentSegment
from core.utils.llm_response_handler import LLMResponseHandler
from core.utils.storage_utils import upload_to_supabase
from core.social_media.twitter import (
    precta_tweet,
    postcta_tweet,
    thread_tweet,
    long_form_tweet,
)
from core.social_media.linkedin import long_form_post
from core.content import image_generator

logger = logging.getLogger(__name__)


async def generate_content(
    content: Content,
    instructions: dict,
    account_profile: AccountProfile,
    supabase_client,
    **kwargs,
) -> Content:
    logger.info(f"Starting generate_content for content_type: {content.content_type}")
    generated_posts = []

    content_type_handlers = {
        "precta_tweet": precta_tweet.generate_precta_tweet,
        "postcta_tweet": postcta_tweet.generate_postcta_tweet,
        "thread_tweet": thread_tweet.generate_thread_tweet,
        "long_form_tweet": long_form_tweet.generate_long_form_tweet,
        "linkedin": long_form_post.generate,
        "image_list": image_generator.generate_image_list,
    }

    for strategy in content.strategy:
        logger.info(f"Processing post number: {strategy.post_number}")

        try:
            if content.content_type in content_type_handlers:
                handler = content_type_handlers[content.content_type]
                raw_response = await handler(
                    strategy.content,
                    strategy.strategy_note,
                    instructions.get(content.content_type, {}),
                    account_profile,
                    **kwargs,
                )
                logger.debug(
                    f"Raw LLM response for {content.content_type}: {raw_response}"
                )

                parsed_content = LLMResponseHandler.process_llm_response(
                    raw_response, "content"
                )
                generated_content = (
                    parsed_content
                    if isinstance(parsed_content, str)
                    else str(parsed_content)
                )
            else:
                raise ValueError(f"Unsupported content type: {content.content_type}")

            generated_posts.append(
                Post(
                    post_number=strategy.post_number,
                    section_type=strategy.section_type,
                    content=generated_content,
                    metadata={"strategy_note": strategy.strategy_note},
                )
            )

        except Exception as e:
            logger.error(
                f"Error generating content for post {strategy.post_number}: {str(e)}"
            )
            logger.exception("Traceback:")

    logger.info("Content generation completed")
    return Content(
        segments=content.segments,
        strategy=content.strategy,
        posts=generated_posts,
        original_content=content.original_content,
        content_type=content.content_type,
        account_id=content.account_id,
        metadata=content.metadata,
    )
