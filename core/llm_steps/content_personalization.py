import json
import logging
import re
from typing import Dict, Any
from core.content.language_model_client import call_language_model
from core.utils.llm_response_handler import LLMResponseHandler
from core.models.account_profile import AccountProfile

logger = logging.getLogger(__name__)

# Import the content type modules
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
        You are an expert content stylist with an unparalleled ability to analyze and mimic writing styles. Your task is to rewrite AI-generated content to perfectly match a user's unique writing style, making it indistinguishable from their authentic posts. Analyze the user's example content for the following elements and apply them to the generated content:

1. Vocabulary choice and complexity
2. Sentence structure and length variety
3. Punctuation usage (frequency and type)
4. Capitalization style (all caps, no caps, sentence case)
5. Emoji usage (frequency, placement, and types)
6. Overall tone (formal, casual, humorous, sarcastic, etc.)
7. Use of abbreviations or acronyms
8. Hashtag usage and style
9. Idioms or colloquialisms
10. Metaphors and analogies
11. Use of rhetorical devices (questions, repetition, etc.)
12. Perspective (first-person vs. third-person)
13. Use of contractions
14. Inclusion of personal anecdotes or experiences
15. Cultural or niche references
16. Technical jargon or industry-specific terms
17. Sentence fragments vs. complete sentences
18. Use of parenthetical asides
19. Frequency of quoted material or external references
20. Paragraph length and structure (for longer posts)
21. Use of lists or bullet points
22. Transition words and phrases
23. Closing remarks or sign-offs
24. Use of emphasis (bold, italic, underline in platforms that support it)
25. Engagement style (asking questions, calls to action)

Carefully analyze how these elements appear in the user's example content and apply them to rewrite the generated content. Maintain the original message and key points while ensuring the style, tone, and voice are an exact match to the user's authentic writing. Pay special attention to platform-specific formatting and conventions for the given {content_type}.

Your rewrite should be so accurate that even the user themselves would believe they wrote it. This level of personalization is critical for maintaining authenticity and user trust in the content generation process.
        """,
    }

    user_message = {
        "role": "user",
        "content": f"""
        User's style example: {style_example}
        
        Content to personalize: {generated_content}
        
        Please personalize the content to match the user's style while maintaining the original message and structure.
        {content_personalization_instructions}

This has to be proper json, so all key and values MUST BE IN DOUBLE QUOTES

        """,
    }

    try:
        # Step 4: Make the LLM call with the system and user messages
        logger.info("Making LLM call for content personalization...")
        response = await call_language_model(system_message, user_message, tier="high")
        logger.info(f"Raw personalized content response: {response}")

        # Step 5: Extract the JSON content between delimiters ~! and !~
        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            logger.info(f"Extracted personalized content: {extracted_content}")

            # Apply further cleaning to remove hidden characters and control characters
            cleaned_content = re.sub(
                r"\s+", " ", extracted_content
            )  # Strip excess whitespace
            cleaned_content = cleaned_content.encode("utf-8", "ignore").decode(
                "utf-8"
            )  # Remove invalid characters
            logger.info(f"Cleaned personalized content: {cleaned_content}")

            try:
                # Attempt to parse the cleaned JSON content
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

        # Validate response_json structure
        if "content_container" not in response_json:
            logger.error(
                f"'content_container' missing in personalized response: {response_json}"
            )
            return {"error": "'content_container' missing", "success": False}

        if not isinstance(response_json["content_container"], list):
            logger.error("content_container in personalized response is not a list")
            return {"error": "Invalid content_container format", "success": False}

        for item in response_json["content_container"]:
            if "post_type" not in item or "post_content" not in item:
                logger.error(f"Invalid item in personalized content_container: {item}")
                return {
                    "error": "Invalid content_container item format",
                    "success": False,
                }

        # Return the personalized content in the exact same structure
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
        # Log the full stack trace of the TypeError or other exceptions to debug the issue
        logger.error(f"Error during content personalization: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}
