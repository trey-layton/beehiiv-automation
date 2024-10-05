from core.utils.llm_response_handler import LLMResponseHandler
from core.models.content import ContentSegment
import logging
import json
from core.content.language_model_client import call_language_model
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


async def analyze_structure(content: str) -> List[ContentSegment]:
    logger.info("Starting structure analysis")
    system_message = {
        "role": "system",
        "content": """You are an advanced content structure analyzer specializing in newsletters. Your task is to break down newsletter content into logical segments without altering or summarizing the content. Follow these guidelines:

1. Identify distinct sections within the newsletter. 
2. Label each segment with a descriptive "type" that reflects its content or function.
3. Include the full, unaltered text of each segment.
4. Do not summarize, paraphrase, or modify the content in any way.
5. Avoid creating arbitrary divisions where the content flows as a cohesive unit.
6. Be aware of formatting cues, headings, and changes in writing style that might indicate segment breaks.
7. Recognize common newsletter elements such as introductions, main stories, conclusions, etc.
8. Do not include headers, footers, or sponsored content.

Format your response exactly as follows:
{"structured_content":[
    {"type":"section_type", "content":"section_content"},
    {"type":"section_type", "content":"section_content"},
    ...
]}
Do not include any additional text or formatting beyond what's inside the "structured_content" array.""",
    }

    user_message = {
        "role": "user",
        "content": f"Analyze the structure of the following newsletter content:\n\n{content}",
    }

    try:
        structured_content = await call_language_model(
            system_message, user_message, tier="medium"
        )
        logger.info("API call for content structuring completed, processing response")
        parsed_content = LLMResponseHandler.process_llm_response(
            structured_content, "structured_content"
        )

        if not isinstance(parsed_content, list):
            parsed_content = [{"type": "main", "content": str(parsed_content)}]

        content_segments = []
        for item in parsed_content:
            if isinstance(item, dict) and "type" in item and "content" in item:
                content_segments.append(
                    ContentSegment(type=item["type"], content=item["content"])
                )
            else:
                logger.warning(f"Skipping invalid content segment: {item}")

        if not content_segments:
            content_segments = [ContentSegment(type="main", content=content)]

        return content_segments

    except Exception as e:
        logger.error(f"Error in structure analysis: {str(e)}")
        logger.exception("Traceback:")
        return [ContentSegment(type="main", content=content)]
