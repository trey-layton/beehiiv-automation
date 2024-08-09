# core/content/improved_llm_flow/final_review.py

import logging
from typing import Union, List, Dict
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def final_review(
    content: Union[str, List[Dict[str, str]]], content_type: str
) -> Union[str, List[Dict[str, str]]]:
    system_message = {
        "role": "system",
        "content": """You are an expert social media manager performing a final review of generated content. Your task is to:
        1. Ensure the content is engaging and aligns with the intended message.
        2. Check for any potential issues or sensitive content that might be problematic.
        3. Make minor improvements to enhance clarity and impact.
        4. Verify that the content adheres to the platform-specific best practices.
        Do not make major changes to the content structure or main points. Return ONLY the final, reviewed version that is ready to post via API, no intro or conclusion text outside of the post content.""",
    }

    user_message = {
        "role": "user",
        "content": f"Perform a final review of this {content_type} content and make any necessary minor improvements:\n\n{content}",
    }

    try:
        response = await call_language_model(system_message, user_message)

        if isinstance(content, list):
            # If the content is a list (e.g., for thread tweets), process each item
            reviewed_content = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    item["text"] = response
                    reviewed_content.append(item)
                else:
                    reviewed_content.append(item)
            return reviewed_content
        else:
            # For single-post content types
            return response

    except Exception as e:
        logger.exception(f"Error in final_review: {str(e)}")
        return content
