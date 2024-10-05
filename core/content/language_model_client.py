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

MODEL_TIERS = {
    "high": {
        "anthropic": {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 200000,
            "max_output_tokens": 8192,
        },
        "openai": {"model": "gpt-4o", "max_tokens": 128000, "max_output_tokens": 4096},
    },
    "medium": {
        "anthropic": {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 200000,
            "max_output_tokens": 4096,
        },
        "openai": {
            "model": "gpt-4o-mini",
            "max_tokens": 128000,
            "max_output_tokens": 4096,
        },
    },
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_language_model(
    system_message: dict, user_message: dict, tier: str = "high"
):
    logger.info(f"Calling language model with tier: {tier}")
    model_config = MODEL_TIERS[tier][LANGUAGE_MODEL_PROVIDER]

    if LANGUAGE_MODEL_PROVIDER == "anthropic":
        return await call_anthropic(system_message, user_message, model_config)
    elif LANGUAGE_MODEL_PROVIDER == "openai":
        return await call_openai(system_message, user_message, model_config)
    else:
        raise ValueError(
            f"Unsupported language model provider: {LANGUAGE_MODEL_PROVIDER}"
        )


async def call_anthropic(system_message: dict, user_message: dict, model_config: dict):
    logger.info("Calling Anthropic API")
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model=model_config["model"],
                max_tokens=model_config["max_output_tokens"],
                temperature=0.7,
                system=system_message["content"],
                messages=[{"role": "user", "content": user_message["content"]}],
            ),
            timeout=300,  # 5 minutes timeout
        )
        logger.info("Anthropic API call successful")
        logger.debug(
            f"Anthropic API response preview: {response.content[0].text[:200]}..."
        )
        return response.content[0].text
    except asyncio.TimeoutError:
        logger.error("Anthropic API call timed out")
        raise
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}")
        raise


async def call_openai(system_message: dict, user_message: dict, model_config: dict):
    logger.info("Calling OpenAI API")
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        completion = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_config["model"],
                messages=[
                    {"role": "system", "content": system_message["content"]},
                    {"role": "user", "content": user_message["content"]},
                ],
                max_tokens=model_config["max_output_tokens"],
                n=1,
                temperature=0.7,
            ),
            timeout=300,  # 5 minutes timeout
        )
        logger.info("OpenAI API call successful")
        logger.debug(
            f"OpenAI API response preview: {completion.choices[0].message.content[:200]}..."
        )
        return completion.choices[0].message.content
    except asyncio.TimeoutError:
        logger.error("OpenAI API call timed out")
        raise
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise
