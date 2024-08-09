import json
import logging
from typing import Union, List, Dict
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def convert_to_json(
    content: Union[str, List[Dict[str, str]]], content_type: str
) -> str:
    system_message = {
        "role": "system",
        "content": "You are an expert in formatting social media posts as JSON. Your task is to take the given content and convert it into a post-ready valid JSON format, where each post is an object in an array. Each object should have 'text' and 'type' fields.",
    }

    example_input = [
        {"text": "This is the main tweet content."},
        {"text": "This is a follow-up tweet with a call to action."},
    ]
    example_output = json.dumps(
        [
            {"text": "This is the main tweet content.", "type": "example_tweet"},
            {
                "text": "This is a follow-up tweet with a call to action.",
                "type": "example_tweet",
            },
        ]
    )

    user_message = {
        "role": "user",
        "content": f"""Convert the following {content_type} content into JSON format. 
Each post should be an object in an array with 'text' and 'type' fields. 
The type for all posts should be '{content_type}'.

Example input:
{json.dumps(example_input, indent=2)}

Example output:
{example_output}

Now, convert this content:
{json.dumps(content, indent=2)}

Please provide only the JSON output, without any additional explanation. Also, make sure to strip out any extra text passed from previous calls that should not be in the final output.""",
    }

    try:
        response = await call_language_model(system_message, user_message)

        logger.debug(f"Raw LLM response: {response}")

        # Attempt to parse the response as JSON
        try:
            json_content = json.loads(response)

            # If the response is not a list, wrap it in a list
            if not isinstance(json_content, list):
                json_content = [json_content]

            # Validate the structure
            for item in json_content:
                if (
                    not isinstance(item, dict)
                    or "text" not in item
                    or "type" not in item
                ):
                    raise ValueError("JSON object is missing required fields")

            # If validation passes, return the JSON string
            return json.dumps(json_content)
        except json.JSONDecodeError:
            logger.warning(
                "LLM response is not valid JSON. Returning the raw response."
            )
            return response

    except Exception as e:
        logger.exception(f"Error in convert_to_json: {str(e)}")
        # Return a default JSON structure in case of any error
        return json.dumps([{"text": str(content), "type": content_type}])
