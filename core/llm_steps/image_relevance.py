import json
import logging
import re
from typing import Dict, Any, List
from core.models.account_profile import AccountProfile
from core.content.language_model_client import call_language_model
from core.llm_steps.content_personalization import get_instructions_for_content_type

logger = logging.getLogger(__name__)


async def check_image_relevance(
    content_data: Dict[str, Any],
    image_urls: List[str],
    account_profile: AccountProfile,
    content_type: str,
) -> Dict[str, Any]:
    """
    Evaluate image relevance and return updated content_data with relevant images if possible.
    If JSON parsing of the LLM's response fails, gracefully fallback to original content_data.
    """
    if not image_urls:
        logger.debug("No images to evaluate for relevance.")
        return content_data

    instructions = get_instructions_for_content_type(content_type)
    image_instructions = instructions.get("image_relevance", "")

    if not image_instructions:
        logger.error(
            f"Missing image relevance instructions for content_type={content_type}. Returning content_data unchanged."
        )
        return content_data

    system_message = {
        "role": "system",
        "content": f"""
        You are an AI assistant specializing in evaluating image relevance for social media posts.
        Be discerning in deciding whether images actually add value to the post. Not every image should be included, 
        especially if it is just branding or generic content unrelated to the text. You do not need to include any images unless they truly add value.
        You can add up to 4 images if relevant.
        
        Your task is to determine which images would enhance specific posts in a {content_type}.
        
        Use this very specific format: {image_instructions}
        
        Return the entire content structure with images assigned to appropriate posts.
        """,
    }

    user_message = {
        "role": "user",
        "content": f"""
        Content to evaluate:
        {json.dumps(content_data, indent=2)}
        
        Available images:
        {json.dumps(image_urls, indent=2)}

        Note that there is a one gif limit, so if the image(s) are gifs, please limit the media to the most relevant gif.
        Do not include any explanatory text. Your answer should be ONLY the requested structure so that we can immediately pass it to the next step in the pipeline without messing up the parsing.
        """,
    }

    try:
        response = await call_language_model(
            system_message, user_message, tier="medium"
        )
        logger.info(f"LLM raw response for image relevance: {response}")

        # Extract JSON from between ~! and !~
        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if not match:
            logger.error("No content found between delimiters (~! !~) in the response.")
            return content_data

        extracted_content = match.group(1).strip()
        cleaned_content = re.sub(r"\s+", " ", extracted_content)
        cleaned_content = re.sub(r"#.*", "", cleaned_content).strip()

        response_json = json.loads(cleaned_content)

        # Just validate basic structure
        if "content_container" not in response_json or not isinstance(
            response_json["content_container"], list
        ):
            logger.error(
                "'content_container' missing or not a list in response from LLM. Returning original content_data."
            )
            return content_data

        logger.info(
            f"Image relevance returning exactly this: {json.dumps(response_json, indent=2)}"
        )
        return response_json

    except Exception as e:
        logger.error(f"Exception in image relevance check: {str(e)}", exc_info=True)
        return content_data
