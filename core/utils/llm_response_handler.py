import re
import json
import logging
from typing import Any, List, Dict, Union

logger = logging.getLogger(__name__)


class LLMResponseHandler:
    @staticmethod
    def extract_text_from_content_blocks(content: Any) -> str:
        if isinstance(content, list):
            return " ".join(block.text for block in content if hasattr(block, "text"))
        elif hasattr(content, "text"):
            return content.text
        elif isinstance(content, str):
            return content
        else:
            return str(content)

    @staticmethod
    def process_llm_response(
        response: Any, key: str
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], str]:
        logger.info(f"Processing LLM response for key: {key}")
        response_text = LLMResponseHandler.extract_text_from_content_blocks(response)
        response_text = response_text.strip()

        try:
            parsed_response = json.loads(response_text)
            if isinstance(parsed_response, dict) and key in parsed_response:
                return parsed_response[key]
            elif isinstance(parsed_response, list):
                return parsed_response
        except json.JSONDecodeError:
            pass

        content_match = re.search(
            rf'"{key}":\s*(\[.*?\]|\{{.*?\}})', response_text, re.DOTALL
        )
        if content_match:
            content = content_match.group(1)
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

        logger.warning(
            f"No valid content structure found for key: {key}. Returning full response."
        )
        return response_text
