import logging
from typing import Dict, Any
from core.content.language_model_client import call_language_model
from core.utils.llm_response_handler import LLMResponseHandler

logger = logging.getLogger(__name__)

# Import the content type map, similar to content_generator.py
from core.social_media.twitter import (
    precta_tweet,
    postcta_tweet,
    thread_tweet,
    long_form_tweet,
)
from core.social_media.linkedin import long_form_post

CONTENT_TYPE_MAP = {
    "precta_tweet": precta_tweet,
    "postcta_tweet": postcta_tweet,
    "thread_tweet": thread_tweet,
    "long_form_tweet": long_form_tweet,
    "linkedin_long_form_post": long_form_post,
}


def get_instructions_for_content_type(content_type: str) -> Dict[str, Any]:
    try:
        module = CONTENT_TYPE_MAP.get(content_type)
        if not module:
            raise ModuleNotFoundError(f"Content type '{content_type}' not found.")
        return module.instructions

    except ModuleNotFoundError as e:
        logging.error(f"Error fetching instructions for {content_type}: {e}")
        return {"content_editing": ""}


async def edit_content(
    generated_content: Dict[str, Any],
    content_type: str,
    instructions: Dict[str, Any] = None,
) -> Dict[str, Any]:
    logger.info(f"Starting content editing for: {content_type}")

    if instructions is None:
        instructions = get_instructions_for_content_type(content_type)

    content_editing_instructions = instructions.get("content_editing", "")

    system_message = {
        "role": "system",
        "content": f"""You are an expert social media copywriter specializing in creating engaging, natural-sounding posts. Your task is to improve the given content based on its type:

1. For all content types:
   - Make the hook super catchy. Make it something bold and daring, throw a big number in, start with "How to" or something that will really make people stop and want to read on.
   - Avoid phrases commonly associated with AI-generated content such as "revolutionizing", "democratizing", "changing the game"
   - Maintain the core message and key points while improving clarity and engagement potential
   - Ensure the content flows naturally and is never choppy, both between subsequent individual posts as part of a larger post and within posts so as to avoid fragments

{content_editing_instructions}""",
    }

    user_message = {
        "role": "user",
        "content": f"Please review and improve the following {content_type} content:\n\n{generated_content}",
    }

    try:
        response = await call_language_model(system_message, user_message, tier="high")
        logger.info(f"Raw edited content for {content_type}: {response}")

        edited_content = LLMResponseHandler.clean_llm_response(response)

        if not edited_content or not isinstance(edited_content, dict):
            logger.warning(
                f"Invalid edited content for {content_type}. Returning original content."
            )
            return generated_content

        return edited_content

    except Exception as e:
        logger.error(f"Error in content editing: {str(e)}")
        return generated_content


# This function can be called from main_process.py
async def run_content_editing(
    generated_content: Dict[str, Any], content_type: str
) -> Dict[str, Any]:
    logger.info(f"Running content editing for {content_type}")

    edited_content = await edit_content(generated_content, content_type)

    return edited_content
