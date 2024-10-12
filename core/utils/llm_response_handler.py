import json
import logging
import re
from typing import Any, Dict, List, Union
from core.models.content import ContentStrategy

logger = logging.getLogger(__name__)


def handle_response(response_content):
    """
    This function tries to parse the response content.
    It first attempts to parse it as JSON, and if it fails, it processes it as raw string.
    """
    parsed_response = None

    # First, try to parse as JSON
    try:
        parsed_response = json.loads(response_content)
        return parsed_response
    except json.JSONDecodeError:
        logger.warning("Response is not valid JSON, processing as raw string")

    # If JSON parsing fails, attempt regex extraction of any JSON structure in the response
    json_str = re.search(r"\{.*\}", response_content, re.DOTALL)
    if json_str:
        try:
            parsed_response = json.loads(json_str.group())
            return parsed_response
        except json.JSONDecodeError:
            logger.warning("Failed to extract valid JSON from string")

    # If no valid JSON found, return the raw response as-is
    return response_content


class LLMResponseHandler:
    @staticmethod
    def process_llm_response(response: Any, stage: str) -> Any:
        if isinstance(response, list):
            return LLMResponseHandler._extract_from_list(response, stage)
        elif isinstance(response, dict):
            return LLMResponseHandler._extract_from_dict(response, stage)
        elif isinstance(response, str):
            try:
                response_json = json.loads(response)
                if isinstance(response_json, list):
                    return LLMResponseHandler._extract_from_list(response_json, stage)
                else:
                    return LLMResponseHandler._extract_from_dict(response_json, stage)
            except json.JSONDecodeError:
                logger.warning(
                    f"Response is not JSON, processing as raw string for stage: {stage}"
                )
                return LLMResponseHandler._extract_from_string(response, stage)
        else:
            logger.error(f"Unsupported response type: {type(response)}")
            return {}

    @staticmethod
    def _extract_from_list(response_list: List[Any], stage: str) -> Any:
        if stage == "content_strategy":
            return [ContentStrategy(**item) for item in response_list]
        else:
            return response_list

    @staticmethod
    def _extract_from_dict(response_dict: Dict[str, Any], stage: str) -> Any:
        if stage == "structure_analysis":
            return response_dict.get("sections", {})
        elif stage == "content_strategy":
            return response_dict.get("strategy", [])
        elif stage == "content_generation":
            return response_dict
        else:
            return response_dict

    @staticmethod
    def _extract_from_string(
        response: str, stage: str
    ) -> Union[Dict[str, str], List[Dict[str, Any]]]:
        logger.warning(f"String parsing not implemented for stage: {stage}")
        return {}

    @staticmethod
    def clean_llm_response(response: str) -> dict:
        """
        Cleans and ensures that the LLM response is properly escaped for safe JSON parsing.
        """
        try:
            logger.info(
                f"Raw LLM Response before cleaning: {response[:100]}"
            )  # Log the raw response
            clean_response = json.loads(response)  # Attempt parsing
            logger.info("Successfully parsed JSON response without modification.")
            return clean_response

        except json.JSONDecodeError:
            logger.error(f"Raw LLM Response: {response}")
            logger.error("JSON parsing failed. Attempting to clean the response.")

            # Now try cleaning the response
            match = re.search(r"(\{.*\}|\[.*\])", response, re.DOTALL)
            if match:
                try:
                    cleaned_json_str = match.group(0)
                    logger.info(
                        f"Extracted JSON string: {cleaned_json_str[:100]}"
                    )  # Log cleaned string
                    cleaned_json = json.loads(cleaned_json_str)
                    logger.info(f"Manually cleaned and parsed response: {cleaned_json}")
                    return cleaned_json
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to parse manually extracted content: {str(e)}"
                    )
                    raise ValueError("Manually extracted content is not valid JSON.")
            else:
                raise ValueError("Unable to extract valid JSON from LLM response.")
