import logging
from core.content.language_model_client import call_language_model
from core.config.feature_toggle import feature_toggle

logger = logging.getLogger(__name__)


async def quality_check_content(
    content: str, api_key: str, max_iterations: int = 3
) -> str:
    if not feature_toggle.is_enabled("USE_QUALITY_CHECK"):
        logger.info("Quality check is disabled")
        return content
    system_message = {
        "role": "system",
        "content": "You are a content quality expert. Your task is to evaluate the given content and determine if it sounds natural and human-like or if it appears robotic and AI-generated. If it needs improvement, provide specific suggestions to make it more authentic and engaging.",
    }

    for iteration in range(max_iterations):
        user_message = {
            "role": "user",
            "content": f"Evaluate the following content and determine if it sounds natural and human-like. If not, provide suggestions for improvement:\n\n{content}",
        }

        response = await call_language_model(api_key, system_message, user_message)

        if isinstance(response, dict) and "evaluation" in response:
            evaluation = response["evaluation"]
            if evaluation.lower() == "approved":
                logger.info(f"Content approved after {iteration + 1} iterations")
                return content
            elif "suggestions" in response:
                logger.info(
                    f"Iteration {iteration + 1}: Improving content based on suggestions"
                )
                content = await improve_content(
                    content, response["suggestions"], api_key
                )
            else:
                logger.warning("Unexpected response format from language model")
                return content
        else:
            logger.error("Invalid response from language model")
            return content

    logger.warning(f"Max iterations ({max_iterations}) reached without approval")
    return content


async def improve_content(content, suggestions, api_key):
    system_message = {
        "role": "system",
        "content": "You are a content improvement expert. Your task is to refine the given content based on the provided suggestions to make it more natural and human-like.",
    }

    user_message = {
        "role": "user",
        "content": f"Improve the following content based on these suggestions:\n\nContent: {content}\n\nSuggestions: {suggestions}",
    }

    response = await call_language_model(api_key, system_message, user_message)

    if isinstance(response, dict) and "improved_content" in response:
        return response["improved_content"]
    else:
        logger.error("Invalid response from language model during content improvement")
        return content
