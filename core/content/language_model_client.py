import asyncio
import logging
import os
from dotenv import load_dotenv
import anthropic
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

LANGUAGE_MODEL_PROVIDER = os.getenv("LANGUAGE_MODEL_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_language_model(system_message: dict, user_message: dict):
    if LANGUAGE_MODEL_PROVIDER == "anthropic":
        return await call_anthropic(system_message, user_message)
    elif LANGUAGE_MODEL_PROVIDER == "openai":
        return await call_openai(system_message, user_message)
    else:
        raise ValueError(
            f"Unsupported language model provider: {LANGUAGE_MODEL_PROVIDER}"
        )


async def call_language_model(system_message: dict, user_message: dict):
    if LANGUAGE_MODEL_PROVIDER == "anthropic":
        return await call_anthropic(system_message, user_message)
    elif LANGUAGE_MODEL_PROVIDER == "openai":
        return await call_openai(system_message, user_message)
    else:
        raise ValueError(
            f"Unsupported language model provider: {LANGUAGE_MODEL_PROVIDER}"
        )


async def call_anthropic(system_message: dict, user_message: dict):
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                temperature=0.7,
                system=system_message["content"],
                messages=[{"role": "user", "content": user_message["content"]}],
            ),
            timeout=120,  # 2 minutes timeout
        )
        return response.content[0].text
    except asyncio.TimeoutError:
        logger.error("Anthropic API call timed out")
        raise
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}")
        raise


async def call_openai(system_message: dict, user_message: dict):
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        completion = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message["content"]},
                    {"role": "user", "content": user_message["content"]},
                ],
                max_tokens=1024,
                n=1,
                temperature=0.3,
            ),
            timeout=120,  # 2 minutes timeout
        )
        return completion.choices[0].message.content
    except asyncio.TimeoutError:
        logger.error("OpenAI API call timed out")
        raise
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise
