from core.utils.llm_response_handler import LLMResponseHandler
from core.models.content import ContentStrategy, Post, ContentSegment
import logging
import json
from typing import List
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def determine_content_strategy(
    content_segments: List[ContentSegment], max_posts: int = 5
) -> List[ContentStrategy]:

    logger.info("Starting content strategy determination")
    system_message = {
        "role": "system",
        "content": """You are an expert content strategist specializing in repurposing newsletter content for social media. Your task is to analyze the structure and content of a newsletter and develop a strategic plan for social media posts. Follow these guidelines:

1. Assess the overall structure of the newsletter (single-section or multi-section).
2. For multi-section newsletters, create one post for each distinct section.
3. For single-section newsletters, create one main post covering the entire content and optionally 1-4 additional posts focusing on specific aspects.
4. Do not alter the original newsletter content.
5. Limit yourself to 5 posts maximum.
6. Do not create posts for introductions, sponsored content, or footers.
7. If there's no clear main story, treat secondary stories as a "top stories" section.

Format your response exactly as follows:
{"social_media_plan":[
    {"post_number":1, "section_type":"type", "content":"post_content"},
    {"post_number":2, "section_type":"type", "content":"post_content"},
    ...
]}
Do not include any additional text or formatting beyond what's inside the "social_media_plan" array.""",
    }

    user_message = {
        "role": "user",
        "content": f"Analyze the following structured newsletter content and create a strategic plan for social media posts:\n\n{json.dumps([segment.dict() for segment in content_segments], indent=2)}",
    }

    try:
        response = await call_language_model(
            system_message, user_message, tier="medium"
        )
        logger.info("API call for social media planning completed, processing response")
        parsed_strategy = LLMResponseHandler.process_llm_response(
            response, "social_media_plan"
        )

        if not isinstance(parsed_strategy, list):
            parsed_strategy = [
                {
                    "post_number": 1,
                    "section_type": "main",
                    "content": str(parsed_strategy),
                }
            ]

        content_strategies = []
        for i, item in enumerate(parsed_strategy[:max_posts], 1):
            if isinstance(item, dict) and "section_type" in item and "content" in item:
                content_strategies.append(
                    ContentStrategy(
                        post_number=i,
                        section_type=item["section_type"],
                        content=item["content"],
                        strategy_note=item.get("strategy_note", ""),
                    )
                )
            else:
                logger.warning(f"Skipping invalid content strategy: {item}")

        return content_strategies

    except Exception as e:
        logger.error(f"Error in content strategy determination: {str(e)}")
        logger.exception("Traceback:")
        return [
            ContentStrategy(
                post_number=1, section_type="main", content=str(content_segments)
            )
        ]
