import logging
from typing import List, Dict, Optional, Union
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def improve_content(
    content: Union[str, List[Dict[str, str]]],
    content_type: str,
) -> Union[str, List[Dict[str, str]]]:
    system_message = {
        "role": "system",
        "content": """You are an expert social media copywriter specializing in creating engaging, natural-sounding posts. Your task is to improve the given post by:
        1. Adding smooth transitions between tweets so that it sounds like a single, coherent narrative
        2. Avoiding phrases commonly associated with AI-generated content ("revolutionizing", "landscape is shifting", "paradise", "rollercoaster", "dive in", "shifting dynamics", "breakthroughs")
        3. Getting rid of fragments and choppy points which seem incoherent or unnatural.
        4. Avoiding too many colons to start tweets (come off as AI-generated)
        5. Matching the author's unique writing style (based on provided examples)
        Maintain the core message, details, and key points of each tweet while making these improvements.""",
    }

    # TODO: When author_style_examples are available, incorporate them into the user_message
    # This will involve analyzing the examples for style characteristics and including
    # instructions in the user_message to match these characteristics.

    user_message = {
        "role": "user",
        "content": f"Improve this {content_type} post: {content}",
    }

    # if author_style_examples:
    # TODO: Implement logic to analyze author_style_examples and extract style characteristics
    # For now, we'll just add them to the user message as-is
    #  user_message[
    #    "content"
    # ] += f"\n\nAuthor's writing style examples:\n{author_style_examples}"

    try:
        response = await call_language_model(system_message, user_message)
        logger.info(
            f"Language model response: {response[:100]}..."
        )  # Log first 100 characters

        if isinstance(content, list) and isinstance(response, list):
            return response
        elif isinstance(content, str) and isinstance(response, str):
            return response
        elif isinstance(response, dict):
            return response.get("improved_content", content)
        else:
            logger.error(
                f"Unexpected response format from language model: {type(response)}"
            )
            return content
    except Exception as e:
        logger.exception(f"Error in improve_content: {str(e)}")
        return content
