import os
import json
import logging
from anthropic import Anthropic
from openai import OpenAI
import re

logger = logging.getLogger(__name__)


def extract_json_from_string(s):
    """Extract a JSON object from a string, even if there's additional text."""
    json_match = re.search(r"\{.*\}", s, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
    return None


def parse_response(response_content):
    """Parse the response content, attempting to extract JSON if present."""
    try:
        # First, try to parse the entire response as JSON
        return json.loads(response_content)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON from the string
        extracted_json = extract_json_from_string(response_content)
        if extracted_json:
            return extracted_json
        else:
            # If no JSON found, return the raw text in a dict
            return {"text": response_content.strip()}


def call_anthropic(api_key, system_message, user_message):
    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            temperature=0.3,
            system=system_message["content"],
            messages=[{"role": "user", "content": user_message["content"]}],
        )
        return parse_response(response.content[0].text)
    except Exception as e:
        logger.error(f"Anthropic API error: {str(e)}")
        raise


def call_openai(api_key, system_message, user_message):
    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message["content"]},
                {"role": "user", "content": user_message["content"]},
            ],
            max_tokens=1024,
            n=1,
            temperature=0.3,
        )
        return parse_response(completion.choices[0].message.content)
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise


def call_language_model(api_key, system_message, user_message, provider="anthropic"):
    logger.info(f"Calling {provider} API with system message: {system_message}")
    logger.info(f"User message (first 500 chars): {user_message['content'][:500]}")

    if provider == "anthropic":
        return call_anthropic(api_key, system_message, user_message)
    elif provider == "openai":
        return call_openai(api_key, system_message, user_message)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
