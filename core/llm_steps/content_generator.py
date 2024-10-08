import importlib
import logging
import re
import json
from typing import Dict, Any
from core.models.account_profile import AccountProfile
from core.utils.llm_response_handler import LLMResponseHandler
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)
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
        # Fetch the instructions module for the given content type
        module = CONTENT_TYPE_MAP.get(content_type)
        if not module:
            raise ModuleNotFoundError(f"Content type '{content_type}' not found.")
        return module.instructions

    except ModuleNotFoundError as e:
        logging.error(f"Error fetching instructions for {content_type}: {e}")
        return {"content_generation": ""}  # Empty instructions as fallback


async def generate_content(
    strategy: Dict[str, Any],
    content_type: str,
    account_profile: AccountProfile,
    web_url: str,
    post_number: int,
    instructions: Dict[str, Any] = None,
) -> Dict[str, Any]:
    logger.info(
        f"Starting content generation for: {content_type}, post number: {post_number}"
    )

    if instructions is None:
        instructions = get_instructions_for_content_type(content_type)

    content_generation_instructions = instructions.get("content_generation", "")
    system_message = {
        "role": "system",
        "content": f"""
        You are an AI assistant specializing in creating engaging social media content.
        Your task is to generate a {content_type} based on the provided newsletter section.
        Follow these guidelines:
        1. Maintain the original meaning and key information from the source content.
        2. Adapt the style to suit the {content_type} format and the account's preferences.
        3. Ensure the content is engaging and suited for the target platform.
        4. {content_generation_instructions}
        
        Format your response as a JSON object with 'type' and 'content' keys. The 'content' should be a list of post objects.
        """,
    }

    user_message = {
        "role": "user",
        "content": f"""
        Generate a {content_type} based on this newsletter section:
        Content: {strategy}
        Account preferences: {account_profile.json()}
        Original content URL: {web_url}
        """,
    }

    try:
        # Call the language model and get the raw response
        response = await call_language_model(system_message, user_message)

        # Log the raw response for inspection
        logger.info(f"Raw LLM response: {response}")

        # Step 1: Try parsing as JSON normally
        try:
            response_json = json.loads(response)
            logger.info("Parsed JSON successfully.")
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON normally, attempting manual extraction.")

            # Step 2: Use a fallback approach to extract the type and content manually
            response_json = {}
            type_match = re.search(r'"type":\s*"([^"]+)"', response)
            content_match = re.search(r'"content":\s*\[(.*)\]', response, re.DOTALL)

            if type_match and content_match:
                response_json["type"] = type_match.group(1)
                response_json["content"] = [
                    {
                        "type": response_json["type"],
                        "content": content_match.group(1).strip(),
                    }
                ]
                logger.info("Manually extracted type and content.")
            else:
                raise ValueError("Unable to extract type or content from the response.")

        # Step 3: Validate the structure of the parsed response
        if "content" not in response_json or not isinstance(
            response_json["content"], list
        ):
            logger.error(f"Invalid response format: {response_json}")
            return {"error": "Invalid response format", "success": False}

        # Step 4: Extract formatted posts
        formatted_posts = []
        for post in response_json["content"]:
            post_type = post.get("type", "")
            post_content = post.get("content", "").strip()
            if post_content:
                formatted_posts.append({"type": post_type, "content": post_content})

        logger.info(
            f"Extracted {len(formatted_posts)} posts for post number {post_number}"
        )

        return {
            "post_number": post_number,
            "content": formatted_posts,
        }

    except Exception as e:
        logger.error(f"Error during content generation: {e}")
        return {"error": str(e), "success": False}
