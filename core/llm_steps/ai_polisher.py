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
    try:
        module = CONTENT_TYPE_MAP.get(content_type)
        if not module:
            raise ModuleNotFoundError(f"Content type '{content_type}' not found.")
        return module.instructions

    except ModuleNotFoundError as e:
        logging.error(f"Error fetching instructions for {content_type}: {e}")
        return {"ai_polish": ""}


def get_platform_from_content_type(content_type: str) -> str:
    return "linkedin" if "linkedin" in content_type else "twitter"


async def ai_polish(
    generated_content: Dict[str, Any],
    account_profile: AccountProfile,
    content_type: str,
    instructions: Dict[str, Any] = None,
) -> Dict[str, Any]:
    logger.info(f"Starting AI polish for: {content_type}")

    # Step 1: Fetch the AI polish instructions for the given content type if not provided
    if instructions is None:
        instructions = get_instructions_for_content_type(content_type)

    ai_polish_instructions = instructions.get("ai_polish", "")

    system_message = {
        "role": "system",
        "content": f"""
        You are an expert editor specializing in refining text to ensure it reads naturally and authentically. Your task is to:

Review the Provided Content: Carefully read the text to identify any overused or common phrases that might make it seem artificially generated or less engaging.

Minimize or Replace Specific Phrases: Focus on minimizing or replacing instances of the following words and phrases, while preserving the original meaning and tone:

it's important [to remember; to note]
due to the fact that
it's imperative
however
overall
in summary
ultimately
delve
underscore
revolutionary/revolutionizing
groundbreaking
game changer
enhance
in the realm of
tapestry
empower
unleash
unlock
elevate
treasure trove
testament
peril
landscape
pertinent
synergy
explore
foster
intricate
folks
pivotal
adhere
amplify
embarked
delved
invaluable
relentless
endeavor
enlightening
insights
esteemed
shed light
cognizant
Preserve the Original Content: Do not change anything else in the text. Maintain the original structure, information, and style.

Maintain the Author's Voice: Ensure that any replacements or adjustments match the tone and voice of the original content.
Don't get rid of any links that are already in the post but never add any more.

No Additional Changes: Do not add any new information, explanations, or comments to the text. Do not get rid of anything else in the post format/content container.
        """,
    }

    user_message = {
        "role": "user",
        "content": f"""
        {ai_polish_instructions}: {generated_content}
        """,
    }

    try:
        logger.info("Making LLM call for AI polishing...")
        response = await call_language_model(system_message, user_message, tier="high")
        logger.info(f"Raw AI polish generation response: {response}")

        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            logger.info(f"Extracted polished content: {extracted_content}")

            cleaned_content = re.sub(r"\s+", " ", extracted_content)
            cleaned_content = cleaned_content.encode("utf-8", "ignore").decode("utf-8")
            logger.info(f"Polished content: {cleaned_content}")

            try:
                response_json = json.loads(cleaned_content)
                logger.info(f"Parsed JSON polished content: {response_json}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing cleaned content as JSON: {e}")
                return {"error": "Failed to parse cleaned content", "success": False}
        else:
            logger.error("No content found between delimiters in AI polish response.")
            return {
                "error": "No content found between delimiters",
                "llm_raw_response": response,
                "success": False,
            }

        # Validate response_json structure
        if "content_container" not in response_json:
            logger.error(
                f"'content_container' missing in AI polish response: {response_json}"
            )
            return {"error": "'content_container' missing", "success": False}

        if not isinstance(response_json["content_container"], list):
            logger.error("content_container in AI polish response is not a list")
            return {"error": "Invalid content_container format", "success": False}

        # Validate content based on type
        if content_type in ["carousel_tweet", "carousel_post"]:
            for item in response_json["content_container"]:
                if "heading" not in item:
                    logger.error(f"Missing heading in carousel slide: {item}")
                    return {
                        "error": "Invalid carousel content format",
                        "success": False,
                    }

                # Validate lengths
                if len(item["heading"]) > 50:
                    logger.warning(f"Heading too long, truncating: {item['heading']}")
                    item["heading"] = item["heading"][:47] + "..."

                if "subheading" in item and len(item["subheading"]) > 100:
                    logger.warning(
                        f"Subheading too long, truncating: {item['subheading']}"
                    )
                    item["subheading"] = item["subheading"][:97] + "..."
        else:
            for item in response_json["content_container"]:
                if "post_type" not in item or "post_content" not in item:
                    logger.error(f"Invalid item in AI polish content_container: {item}")
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
            f"Successfully generated AI polished posts for post number {generated_content.get('post_number')}"
        )
        return result

    except Exception as e:
        logger.error(f"Error during AI polish: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}
