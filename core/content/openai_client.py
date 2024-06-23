import json
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


def setup_openai(api_key):
    return OpenAI(api_key=api_key)


def call_openai(api_key, system_message, user_message):
    logger.info(f"Calling OpenAI API with system message: {system_message}")
    logger.info(f"User message (first 500 chars): {user_message['content'][:500]}")
    client = setup_openai(api_key)

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"{system_message['content']} Remember to output the response in JSON format.",
            },
            {"role": "user", "content": user_message["content"]},
        ],
        max_tokens=280,
        n=1,
        temperature=0.3,
    )

    response_content = completion.choices[0].message.content
    try:
        return json.loads(response_content)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON response from OpenAI API: {response_content}")
