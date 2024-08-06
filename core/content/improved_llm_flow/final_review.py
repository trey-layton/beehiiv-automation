import json
import logging
from typing import Dict, Any
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def final_review(content: Dict[str, Any]) -> Dict[str, Any]:
    system_message = {
        "role": "system",
        "content": """You are an expert social media manager and content reviewer. Your task is to perform a final review of the generated content, ensuring it's ready for posting. Check for:

        1. Content quality and engagement potential
        2. Proper formatting and structure
        3. Correct inclusion of links and hashtags
        4. Adherence to platform-specific rules (e.g., character limits for Twitter)
        5. Consistency between main content and CTA
        6. Overall flow and coherence of the content

        If any issues are found, provide specific corrections, and then return your response in the exact same format that you received it in. If no issues are found, return the content as-is in valid JSON format.""",
    }

    user_message = {
        "role": "user",
        "content": f"""Please review the following content for posting:

        {json.dumps(content, indent=2)}

        If any improvements are needed, please provide the corrected version in valid JSON format. If no changes are needed, return the content in its current form as a valid JSON string.""",
    }

    try:
        response = await call_language_model(system_message, user_message)

        # Try to extract JSON from the response
        try:
            # Find the start and end of the JSON object in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                revised_content = json.loads(json_str)
                logger.info("Successfully parsed JSON from final review response.")
                return revised_content
            else:
                raise ValueError("No valid JSON object found in the response")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"Failed to parse JSON from final review response. Error: {str(e)}"
            )
            logger.error(f"Raw response: {response}")

            # Check if the response indicates no changes are needed
            if "looks good overall and is ready for posting" in response.lower():
                logger.info("No changes required in final review.")
                return content

            # If it's not a recognized response, return the original content
            logger.warning(
                "Unrecognized response from final review. Returning original content."
            )
            return content

    except Exception as e:
        logger.exception(f"Error in final_review: {str(e)}")
        return content
