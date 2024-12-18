import logging
import json
import re
from typing import Dict, Any, List
from core.models.account_profile import AccountProfile
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)

# Static mapping for content type modules
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
logger.info("Initializing CONTENT_TYPE_MAP with values:")
for k, v in CONTENT_TYPE_MAP.items():
    logger.info(f"{k}: {v}")

try:
    from core.social_media.twitter.carousel_tweet import (
        instructions as twitter_carousel_instructions,
    )
    from core.social_media.linkedin.carousel_post import (
        instructions as linkedin_carousel_instructions,
    )

    logger.info("Successfully imported carousel instruction modules")
except Exception as e:
    logger.error(f"Failed to import carousel modules: {str(e)}")


def get_instructions_for_content_type(content_type: str) -> Dict[str, Any]:
    logger.info("get_instructions_for_content_type called in content_generator.py")
    try:
        module_name = CONTENT_TYPE_MAP.get(content_type)
        logger.info(f"Module name: {module_name}")

        if not module_name:
            raise ModuleNotFoundError(f"Content type '{content_type}' not found.")

        module = __import__(module_name, fromlist=["instructions"])
        logger.info(f"Module imported: {module}")
        instructions = getattr(module, "instructions")
        logger.info(f"Instructions retrieved: {instructions}")

        return instructions

    except Exception as e:
        logger.error(f"Error in content_generator.py get_instructions: {str(e)}")
        raise


def replace_urls_in_content(
    content: str, account_profile: AccountProfile, web_url: str
) -> str:
    """
    Replace URL template variables in content with actual values.

    Args:
        content: String containing template variables
        account_profile: AccountProfile object containing replacement values
        web_url: String containing the article URL

    Returns:
        String with template variables replaced with actual values
    """
    replacements = {
        "{account_profile.subscribe_url}": account_profile.subscribe_url,
        "{web_url}": web_url,
        # Add any other URL template variables here
    }

    result = content
    for template, value in replacements.items():
        if value:  # Only replace if we have a non-None value
            result = result.replace(template, value)
        else:
            logger.warning(f"Missing value for URL template: {template}")
            # Optionally handle missing URLs - could remove the template or replace with a default
            result = result.replace(template, "")

    return result


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
        4. Replace {account_profile.subscribe_url} (including the brackets) with the actual subscription link.
        5. Replace {web_url} (including the brackets) with the actual article link.
        6. {content_generation_instructions}
        
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
        response = await call_language_model(
            system_message, user_message, tier="medium"
        )
        logger.info(f"LLM raw response: {response}")

        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if not match:
            logger.error("No content found between delimiters in response.")
            return {
                "error": "No content found between delimiters",
                "llm_raw_response": response,
                "success": False,
            }

        extracted_content = match.group(1).strip()
        cleaned_content = re.sub(r"\s+", " ", extracted_content)
        cleaned_content = cleaned_content.encode("utf-8", "ignore").decode("utf-8")

        try:
            response_json = json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing cleaned content as JSON: {e}")
            return {"error": "Failed to parse cleaned content", "success": False}

        if "content_container" not in response_json:
            logger.error(f"'content_container' missing in response: {response_json}")
            return {"error": "'content_container' missing", "success": False}

        if not isinstance(response_json["content_container"], list):
            logger.error("content_container is not a list")
            return {"error": "Invalid content_container format", "success": False}

        # Validate carousel content structure
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

        # Replace URL templates
        for item in response_json["content_container"]:
            if content_type in ["carousel_tweet", "carousel_post"]:
                if "heading" in item:
                    item["heading"] = replace_urls_in_content(
                        item["heading"], account_profile, web_url
                    )
                if "subheading" in item:
                    item["subheading"] = replace_urls_in_content(
                        item["subheading"], account_profile, web_url
                    )
            else:
                if "post_type" not in item or "post_content" not in item:
                    logger.error(f"Invalid item in content_container: {item}")
                    return {
                        "error": "Invalid content_container item format",
                        "success": False,
                    }
                item["post_content"] = replace_urls_in_content(
                    item["post_content"], account_profile, web_url
                )

        result = {
            "post_number": post_number,
            "content_type": response_json.get("content_type", content_type),
            "content_container": response_json["content_container"],
        }

        logger.info(f"Successfully generated content for post number {post_number}")
        return result

    except Exception as e:
        logger.error(f"Error during content generation: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}
