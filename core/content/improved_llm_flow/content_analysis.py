import logging
from typing import Dict, Any
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def analyze_content(content: str, account_profile: Any) -> Dict[str, Any]:
    logger.info("Starting content analysis")

    system_message = {
        "role": "system",
        "content": """You are an expert content analyst. Your task is to analyze the structure and content of a newsletter and provide a detailed breakdown. Focus on the following aspects:

1. Newsletter structure: Identify distinct sections, their purposes, and how they relate to each other.
2. Content type classification: Determine the overall type of the newsletter (e.g., informational, narrative, listicle, etc.).
3. Main points and value proposition: Identify the key takeaways and the primary value offered to readers.
4. Overall tone and style: Describe the writing style, level of formality, and emotional tone of the content.

Provide your analysis in a structured JSON format.""",
    }

    user_message = {
        "role": "user",
        "content": f"Analyze the following newsletter content:\n\n{content}",
    }

    try:
        response = await call_language_model(system_message, user_message)
        logger.info("Content analysis completed successfully")
        logger.debug(f"Analysis result: {response}")
        return response
    except Exception as e:
        logger.error(f"Error during content analysis: {str(e)}")
        raise


async def prioritize_content(
    analysis_result: Dict[str, Any], account_profile: Any
) -> Dict[str, Any]:
    logger.info("Starting content prioritization")

    system_message = {
        "role": "system",
        "content": """You are an expert content strategist. Your task is to prioritize the most relevant content from a newsletter analysis for social media posting. Consider the following factors:

1. User's custom focus (if available)
2. Current date and time relevance
3. Potential for engagement on social media
4. Alignment with the newsletter's main value proposition

Provide your prioritization in a structured JSON format, including reasoning for your choices.""",
    }

    user_message = {
        "role": "user",
        "content": f"Prioritize the content based on this analysis:\n\n{analysis_result}\n\nUser's custom focus: {account_profile.custom_focus if hasattr(account_profile, 'custom_focus') else 'Not specified'}",
    }

    try:
        response = await call_language_model(system_message, user_message)
        logger.info("Content prioritization completed successfully")
        logger.debug(f"Prioritization result: {response}")
        return response
    except Exception as e:
        logger.error(f"Error during content prioritization: {str(e)}")
        raise


async def analyze_and_prioritize_content(
    content: str, account_profile: Any
) -> Dict[str, Any]:
    analysis_result = await analyze_content(content, account_profile)
    prioritized_content = await prioritize_content(analysis_result, account_profile)

    return {"analysis": analysis_result, "prioritization": prioritized_content}
