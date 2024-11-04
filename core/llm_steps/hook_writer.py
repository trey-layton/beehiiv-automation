import json
import logging
import re
from typing import Dict, Any
from core.content.language_model_client import call_language_model
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
        return {"hook_writing": ""}


def get_platform_from_content_type(content_type: str) -> str:
    return "linkedin" if "linkedin" in content_type else "twitter"


async def write_hooks(
    generated_content: Dict[str, Any],
    account_profile: AccountProfile,
    content_type: str,
    instructions: Dict[str, Any] = None,
) -> Dict[str, Any]:
    logger.info(f"Starting hook generation for: {content_type}")

    # Step 1: Fetch the hook writing instructions for the given content type if not provided
    if instructions is None:
        instructions = get_instructions_for_content_type(content_type)

    hook_writing_instructions = instructions.get("hook_writing", "")

    system_message = {
        "role": "system",
        "content": f"""
        You are an expert social media copywriter. Evaluate the existing prompt. If it is not already strong, replace it. DO NOT CHANGE ANY OTHER TEXT OTHER THAN THE HOOK.

Analyze the Entire Post to understand the author's style, tone, voice, and the main message of the post.

Use these templates as guides:

Hook Templates (Use as Guide):
    1. Authority by Association: "[Person/company] achieved X. [Why you should care]. Here's a breakdown:"
    - Why it works: Credibility and authority capture attention by borrowing someone else's.
    - Example: "Harry Potter is the #2 best-selling book of the last quarter century. Only behind The Bible. And JK Rowling used 1 storytelling framework for the entire series. Here's a breakdown:"

    2. Overcoming Adversity: "I had [problem]. Here's how I overcame it (so you can too):"
    - Why it works: Everyone seeks solutions and loves transformation stories.
    - Example: "It took me 11 years to overcome my social anxiety. If you're a man struggling with confidence, read this:"

    3. Most People Suck: "Most [group or advice] sucks. Here's how you won't:"
    - Why it works: Appeals to ego; nobody wants to be in the failing group.
    - Example: "Most people suck at storytelling. Here's an easy trick for telling better stories:"

    4. The Guide... But With a Twist: "How to achieve [desire] without [undesirable limitation or action]"
    - Why it works: Curiosity gets the click; people want solutions without drawbacks.
    - Example: "How to Get Rich (without getting lucky):"

    5. The Leg Work: "I've invested [energy, time, money] doing Y. Here's everything I've learned."
    - Why it works: People value pre-compiled knowledge and effort.
    - Example: "I analyzed 100s of landing pages to give you some inspiration. Here are 34 of the very best:"

    6. This Skill is Awesome: "Learning [skill] gives [benefit]. Here're X [tips] that will help you [achieve result]"
    - Why it works: Fuels desire and provides actionable steps.
    - Example: "Copywriting is a key marketing skill. Learning it will make you millions. Here are 10 copywriting tips that will increase clicks and conversions on your website, ads, emails, and more:"

    7. The Curator: "Used right, X is a [massive benefit to reader]. Here're X [resources I've gathered]"
    - Why it works: Offers curated knowledge, saving readers time and effort.
    - Example: "If you're looking in the right places, the internet is a treasure trove. The best internet gems you've never heard of:"

    8. The Enemy: "[Enemy] is costing you [money, time, energy, status]. Here's what you actually need to know:"
    - Why it works: Triggers 'Us vs Them' mentality and loss aversion.
    - Example: "Men: 99% of fitness advice exists to make you fat and slow. Here's 5 exercises that will give you the physique your family deserves and a strength of a spartan to boot."

    9. Accomplishments: "I [achieved goal] [Optional: without Y]. Here's my [advice, lessons, process]:"
    - Why it works: Sharing progress and achievements inspires others.
    - Example: "I've done over $1M in income in 2 years as an entrepreneur. And I didn't write a single line of code. My 12 "must use" no-code tools:"

    10. Habits: "X [good/bad/little known/secret] habits that [achieve pleasure or remove pain]"
        - Why it works: Taps into pursuit of pleasure or pain removal; habits are cornerstone of change.
        - Example: "7 bad habits that are preventing you from having the life you want:"

Refer to the provided hook templates to structure your hook, but ensure it feels natural within the author's style and the content of the post. The new hook must flow naturally into the rest of the content, matching the author's writing style perfectly.

Don't get rid of any links that are already in the post but never add any more.

No Additional Content: Do not add explanations, comments, or any additional content to your response.

Your output must be identical to the input in every way except for the first sentence. This is critical for the rest of the content generation pipeline to function correctly.
        """,
    }

    user_message = {
        "role": "user",
        "content": f"""
        Here's the original {content_type} post: {generated_content} and your formatting requirements: {hook_writing_instructions}
        """,
    }

    try:
        logger.info("Making LLM call for hook generation...")
        response = await call_language_model(system_message, user_message, tier="high")
        logger.info(f"Raw hook generation response: {response}")

        # Extract the JSON content between delimiters ~! and !~
        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            logger.info(f"Extracted hooks: {extracted_content}")

            # Apply cleaning to remove hidden characters and control characters
            cleaned_content = re.sub(r"\s+", " ", extracted_content)
            cleaned_content = cleaned_content.encode("utf-8", "ignore").decode("utf-8")
            logger.info(f"Cleaned hooks: {cleaned_content}")

            try:
                response_json = json.loads(cleaned_content)
                logger.info(f"Parsed JSON hooks: {response_json}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing cleaned content as JSON: {e}")
                return {"error": "Failed to parse cleaned content", "success": False}
        else:
            logger.error("No content found between delimiters in hook response.")
            return {
                "error": "No content found between delimiters",
                "llm_raw_response": response,
                "success": False,
            }

        # Validate response_json structure
        if "content_container" not in response_json:
            logger.error(
                f"'content_container' missing in hook response: {response_json}"
            )
            return {"error": "'content_container' missing", "success": False}

        if not isinstance(response_json["content_container"], list):
            logger.error("content_container in hook response is not a list")
            return {"error": "Invalid content_container format", "success": False}

        for item in response_json["content_container"]:
            if "post_type" not in item or "post_content" not in item:
                logger.error(f"Invalid item in hook content_container: {item}")
                return {
                    "error": "Invalid content_container item format",
                    "success": False,
                }

        # Return the hooks in the exact same structure
        result = {
            "post_number": generated_content.get("post_number"),
            "content_type": response_json.get("content_type", content_type),
            "content_container": response_json["content_container"],
        }

        logger.info(
            f"Successfully generated hooks for post number {generated_content.get('post_number')}"
        )
        return result

    except Exception as e:
        logger.error(f"Error during hook generation: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}
