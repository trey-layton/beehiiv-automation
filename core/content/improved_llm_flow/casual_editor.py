import logging
from typing import Union, List, Dict
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def casual_edit(
    content: Union[str, List[Dict[str, str]]],
    content_type: str,
    target_casualness: int = 7,
) -> Union[str, List[Dict[str, str]]]:
    system_message = {
        "role": "system",
        "content": """You are an expert social media editor specializing in creating content with varying levels of casualness. You can accurately assess the casualness of text on a scale of 1-10, where 1 is extremely formal and 10 is very casual. You can also adjust the casualness of text to a specified target level.""",
    }

    async def assess_casualness(text):
        assess_message = {
            "role": "user",
            "content": f"Rate the following text on a scale of 1-10 for casualness (1 is extremely formal, 10 is very casual):\n\n{text}\n\nProvide only the numeric rating.",
        }
        response = await call_language_model(system_message, assess_message)
        try:
            return int(response.strip())
        except ValueError:
            logger.error(f"Failed to parse casualness rating: {response}")
            return 5  # Default to middle value if parsing fails

    async def adjust_casualness(text, current_level, target_level):
        adjust_message = {
            "role": "user",
            "content": f"The following text has a casualness rating of {current_level}. Rewrite it to have a casualness rating of {target_level}, maintaining the core message and key points:\n\n{text}",
        }
        return await call_language_model(system_message, adjust_message)

    try:
        if isinstance(content, list):
            edited_content = []
            for item in content:
                text = item["text"]
                current_level = await assess_casualness(text)
                if current_level != target_casualness:
                    text = await adjust_casualness(
                        text, current_level, target_casualness
                    )
                edited_content.append({"text": text})
            return edited_content
        elif isinstance(content, str):
            current_level = await assess_casualness(content)
            if current_level != target_casualness:
                content = await adjust_casualness(
                    content, current_level, target_casualness
                )
            return content
        else:
            logger.error(f"Unsupported content type: {type(content)}")
            return content

    except Exception as e:
        logger.exception(f"Error in casual_edit: {str(e)}")
        return content
