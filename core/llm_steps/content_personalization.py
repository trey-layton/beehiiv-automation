import json
import logging
import re
from typing import Dict, Any
from core.content.language_model_client import call_language_model
from core.models.account_profile import AccountProfile

logger = logging.getLogger(__name__)

CONTENT_TYPE_MAP = {
    "precta_tweet": "core.social_media.twitter.precta_tweet",
    "postcta_tweet": "core.social_media.twitter.postcta_tweet",
    "thread_tweet": "core.social_media.twitter.thread_tweet",
    "long_form_tweet": "core.social_media.twitter.long_form_tweet",
    "long_form_post": "core.social_media.linkedin.long_form_post",
    "image_list": "core.social_media.image_list",
    "carousel_tweet": "core.social_media.twitter.carousel_tweet",
    "carousel_post": "core.social_media.linkedin.carousel_post",
}


def get_instructions_for_content_type(content_type: str) -> Dict[str, Any]:
    logger.info(
        "get_instructions_for_content_type called in content_personalization.py"
    )
    try:
        module_name = CONTENT_TYPE_MAP.get(content_type)
        logger.info(f"Getting instructions for module: {module_name}")

        if not module_name:
            raise ModuleNotFoundError(f"Content type '{content_type}' not found.")

        # Import the module first, then get instructions
        module = __import__(module_name, fromlist=["instructions"])
        return getattr(module, "instructions")

    except ModuleNotFoundError as e:
        logging.error(f"Error fetching instructions for {content_type}: {e}")
        return {"content_personalization": ""}


def get_platform_from_content_type(content_type: str) -> str:
    return "linkedin" if "linkedin" in content_type else "twitter"


async def personalize_content(
    generated_content: Dict[str, Any],
    account_profile: AccountProfile,
    content_type: str,
    instructions: Dict[str, Any] = None,
) -> Dict[str, Any]:
    logger.info(f"Starting content personalization for: {content_type}")

    # Step 1: Fetch the personalization instructions for the given content type
    if instructions is None:
        instructions = get_instructions_for_content_type(content_type)

    content_personalization_instructions = instructions.get(
        "content_personalization", ""
    )

    # Step 2: Prepare the platform-specific example style
    platform = get_platform_from_content_type(content_type)
    style_example = getattr(account_profile, f"example_{platform}", "")

    # If no specific style example is found, use the newsletter content as a fallback
    if not style_example:
        logger.info(f"No {platform} style example found. Using newsletter content.")
        style_example = account_profile.newsletter_content

    system_message = {
        "role": "system",
        "content": f"""
        You are an expert content stylist with a keen ability to analyze and mimic writing styles. Your task is to rewrite the 'post_content' in the provided JSON input to perfectly match the user's unique writing style, making it indistinguishable from their authentic posts. Analyze the user's example content and focus on key stylistic elements such as:
Tone (e.g., formal, casual, humorous)
Vocabulary and language complexity
Sentence and paragraph structure and length
Punctuation and capitalization (ex: do they only use lowercase letters? )
Use of personal anecdotes or rhetorical devices (and which ones)
Use of emojis or hashtags?
Specific styling tools like dashes, colons, etc
Maintain the original message and key points while ensuring the style, tone, and voice are an exact match to the user's authentic writing. Keep the rest of the JSON structure and content unchanged. Keep all of your reasoning to yourself (only output the requested structure)
        """,
    }

    user_message = {
        "role": "user",
        "content": f"""
        {content_personalization_instructions}
        Here is the unedited post: {generated_content}
        and an example of the author's style for this platform: {style_example}.
        Don't get rid of any links that are already in the post but never add any more.
        """,
    }

    try:
        logger.info("Making LLM call for content personalization...")
        response = await call_language_model(system_message, user_message, tier="high")
        logger.info(f"Raw personalized content response: {response}")

        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            logger.info(f"Extracted personalized content: {extracted_content}")

            cleaned_content = re.sub(r"\s+", " ", extracted_content)
            cleaned_content = cleaned_content.encode("utf-8", "ignore").decode("utf-8")
            logger.info(f"Cleaned personalized content: {cleaned_content}")

            try:
                response_json = json.loads(cleaned_content)
                logger.info(f"Parsed JSON personalized content: {response_json}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing cleaned content as JSON: {e}")
                return {"error": "Failed to parse cleaned content", "success": False}
        else:
            logger.error(
                "No content found between delimiters in personalized response."
            )
            return {
                "error": "No content found between delimiters",
                "llm_raw_response": response,
                "success": False,
            }

        if "content_container" not in response_json:
            logger.error(
                f"'content_container' missing in personalized response: {response_json}"
            )
            return {"error": "'content_container' missing", "success": False}

        if not isinstance(response_json["content_container"], list):
            logger.error("content_container in personalized response is not a list")
            return {"error": "Invalid content_container format", "success": False}

        # Validate based on content type
        if content_type in ["carousel_tweet", "carousel_post"]:
            max_slides = 8 if content_type == "carousel_post" else 4
            if len(response_json["content_container"]) > max_slides:
                logger.warning(
                    f"Too many slides ({len(response_json['content_container'])}), truncating to {max_slides}"
                )
                response_json["content_container"] = response_json["content_container"][
                    :max_slides
                ]

            for idx, item in enumerate(response_json["content_container"]):
                if "heading" not in item:
                    logger.error(f"Missing heading in slide {idx}")
                    return {
                        "error": f"Missing heading in slide {idx}",
                        "success": False,
                    }

                # Validate content lengths
                if len(item["heading"]) > 50:
                    logger.warning(f"Heading too long in slide {idx}, truncating")
                    item["heading"] = item["heading"][:47] + "..."

                if "subheading" in item and len(item["subheading"]) > 100:
                    logger.warning(f"Subheading too long in slide {idx}, truncating")
                    item["subheading"] = item["subheading"][:97] + "..."
        else:
            for item in response_json["content_container"]:
                if "post_type" not in item or "post_content" not in item:
                    logger.error(
                        f"Invalid item in personalized content_container: {item}"
                    )
                    return {
                        "error": "Invalid content_container item format",
                        "success": False,
                    }

        result = {
            "post_number": generated_content.get("post_number"),
            "content_type": response_json.get("content_type", content_type),
            "content_container": response_json["content_container"],
        }

        logger.info(
            f"Successfully personalized content for post number {generated_content.get('post_number')}"
        )
        return result

    except Exception as e:
        logger.error(f"Error during content personalization: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}
