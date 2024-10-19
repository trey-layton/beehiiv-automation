import logging
import json
import re
from typing import Dict, Any
from core.models.account_profile import AccountProfile
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)

# Static mapping for content type modules
CONTENT_TYPE_MAP = {
    "precta_tweet": "core.social_media.twitter",
    "postcta_tweet": "core.social_media.twitter",
    "thread_tweet": "core.social_media.twitter",
    "long_form_tweet": "core.social_media.twitter",
    "long_form_post": "core.social_media.linkedin",
}


def get_instructions_for_content_type(content_type: str) -> Dict[str, Any]:
    try:
        module_name = CONTENT_TYPE_MAP.get(content_type)
        if not module_name:
            raise ModuleNotFoundError(f"Content type '{content_type}' not found.")
        module = __import__(module_name, fromlist=[content_type])
        instructions = getattr(module, content_type).instructions
        if not instructions.get("content_generation"):
            raise ValueError(
                f"No content_generation instructions found for {content_type}"
            )
        return instructions
    except ModuleNotFoundError as e:
        logger.error(f"Error fetching instructions for {content_type}: {e}")
        return {"content_generation": ""}
    except Exception as e:
        logger.error(f"Unexpected error loading instructions for {content_type}: {e}")
        return {"content_generation": ""}


async def generate_content(
    strategy: Dict[str, Any],
    content_type: str,
    account_profile: AccountProfile,
    web_url: str,
    post_number: int,
) -> Dict[str, Any]:
    logger.info(
        f"Starting content generation for: {content_type}, post number: {post_number}"
    )

    # Load instructions for this content type
    instructions = get_instructions_for_content_type(content_type)
    content_generation_instructions = instructions.get("content_generation", "")

    if not content_generation_instructions:
        logger.error(f"Missing content generation instructions for {content_type}")
        return {"error": "Missing content generation instructions", "success": False}
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
        Wrap your response with the delimiters ~! and !~ to ensure correct parsing as shown in the example format.
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
        logger.info("Making LLM call with system and user message...")
        response = await call_language_model(system_message, user_message)

        # Log the raw LLM response for debugging purposes
        logger.info(f"LLM raw response: {response}")

        # Extract the JSON content between delimiters ~! and !~
        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            logger.info(f"Extracted content: {extracted_content}")

            # Apply further cleaning to remove hidden characters and control characters
            cleaned_content = re.sub(
                r"\s+", " ", extracted_content
            )  # Strip excess whitespace
            cleaned_content = cleaned_content.encode("utf-8", "ignore").decode(
                "utf-8"
            )  # Remove invalid characters
            logger.info(f"Cleaned content: {cleaned_content}")

            try:
                # Attempt to parse the cleaned JSON content
                response_json = json.loads(cleaned_content)
                logger.info(f"Parsed JSON response: {response_json}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing cleaned content as JSON: {e}")
                return {"error": "Failed to parse cleaned content", "success": False}
        else:
            logger.error("No content found between delimiters in response.")
            return {
                "error": "No content found between delimiters",
                "llm_raw_response": response,
                "success": False,
            }

        # Validate response_json structure
        if "content_container" not in response_json:
            logger.error(f"'content_container' missing in response: {response_json}")
            return {"error": "'content_container' missing", "success": False}

        if not isinstance(response_json["content_container"], list):
            logger.error("content_container is not a list")
            return {"error": "Invalid content_container format", "success": False}

        for item in response_json["content_container"]:
            if "post_type" not in item or "post_content" not in item:
                logger.error(f"Invalid item in content_container: {item}")
                return {
                    "error": "Invalid content_container item format",
                    "success": False,
                }

        result = {
            "post_number": post_number,
            "content_type": response_json.get("content_type", content_type),
            "content_container": response_json["content_container"],
        }

        logger.info(f"Successfully generated content for post number {post_number}")
        return result

    except Exception as e:
        # Log the full stack trace of the TypeError or other exceptions to debug the issue
        logger.error(f"Error during content generation: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}
