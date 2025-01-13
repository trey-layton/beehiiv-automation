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
logger.setLevel(logging.DEBUG)  # <-- ADD: Ensure we’re at debug level

MODEL_TIERS = {
    "high": {
        "anthropic": {
            "model": "claude-3-5-sonnet-20241022",
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
    "o1-preview": {
            "model": "o1-preview",
            "max_tokens": 128000,
            "max_output_tokens": 4096,
        },
    },
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_language_model(
    system_message: dict,
    user_message: dict,
    tier: str = "high",
    provider_override: str = None,
):
    """
    Main entry point for calling either Anthropics or OpenAI, based on tier & provider override.
    """
    logger.info("=== Entering call_language_model ===")  # <-- ADD
    logger.info(f"Requested tier: {tier}")  # <-- ADD
    logger.info(f"provider_override: {provider_override}")  # <-- ADD
    logger.info(f"LANGUAGE_MODEL_PROVIDER env: {LANGUAGE_MODEL_PROVIDER}")  # <-- ADD

    try:
        provider = provider_override if provider_override else LANGUAGE_MODEL_PROVIDER
        logger.info(f"Final provider to be used: {provider}")  # <-- ADD

        # Wrap in a try/except to catch KeyError for MODEL_TIERS lookups
        try:
            model_config = MODEL_TIERS[tier][provider]
        except KeyError as ke:
            logger.error("KeyError when accessing MODEL_TIERS:")
            logger.error(f"tier: {tier}, provider: {provider}")
            logger.exception("Traceback:")
            raise

        # Convert the content fields to strings if not already
        system_content = str(system_message.get("content", ""))
        user_content = str(user_message.get("content", ""))

        logger.info(f"Calling language model ({provider}) with tier: {tier}")
        logger.debug(f"System message content: {system_content[:300]}...")  # truncated
        logger.debug(f"User message content: {user_content[:300]}...")  # truncated

        if provider == "anthropic":
            return await call_anthropic(system_content, user_content, model_config)
        elif provider == "openai":
            return await call_openai(system_content, user_content, model_config)
        else:
            raise ValueError(f"Unsupported language model provider: {provider}")
    except Exception as e:
        logger.error("Caught exception in call_language_model:")
        logger.error(str(e))
        logger.exception("Full traceback from call_language_model:")
        raise


async def call_anthropic(system_content: str, user_content: str, model_config: dict):
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model=model_config["model"],
                max_tokens=model_config["max_output_tokens"],
                temperature=0.5,
                system=system_content,
                messages=[{"role": "user", "content": user_content}],
            ),
            timeout=300,  # 5 minutes timeout
        )
        logger.debug(f"Anthropic API full response: {response}")
        if response.content and len(response.content) > 0:
            logger.debug(
                f"Anthropic API response preview: {response.content[0].text[:200]}..."
            )
        return response.content[0].text
    except asyncio.TimeoutError:
        logger.error("Anthropic API call timed out")
        raise
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}")
        logger.exception("Full traceback from call_anthropic:")
        raise


async def call_openai(system_content: str, user_content: str, model_config: dict):
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        # For o1 family models, combine system and user content into a single user message
        if "o1" in model_config["model"]:
            combined_content = (
                f"{system_content}\n\n{user_content}"
                if system_content
                else user_content
            )
            messages = [{"role": "user", "content": combined_content}]
            # o1 models have specific parameter requirements
            # Use only the essential parameters for o1-preview
            params = {
                "model": model_config["model"],
                "messages": messages,
            }

            # Log the exact request we're about to send
            logger.info(f"O1 Request - Model: {model_config['model']}")
            logger.info(f"O1 Request - Messages: {messages}")
            logger.info(f"O1 Request - Parameters: {params}")
            logger.info(
                f"O1 Request - Combined content length: {len(combined_content)}"
            )
            logger.info(
                f"O1 Request - Combined content preview: {combined_content[:500]}..."
            )

        else:
            messages = [
                {
                    "role": "developer",
                    "content": [{"type": "text", "text": system_content}],
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_content}],
                },
            ]
            params = {
                "model": model_config["model"],
                "messages": messages,
                "max_tokens": model_config["max_output_tokens"],
                "n": 1,
                "temperature": 0.7,
            }

        # Add detailed logging before API call
        logger.debug(f"OpenAI API request parameters: {params}")

        completion = await asyncio.wait_for(
            client.chat.completions.create(**params),
            timeout=300,  # 5 minutes
        )

        # Add more comprehensive logging of the response
        logger.info(f"OpenAI API - Response type: {type(completion)}")
        try:
            response_dict = completion.model_dump()  # Newer versions
        except AttributeError:
            try:
                response_dict = completion.dict()  # Older versions
            except AttributeError:
                response_dict = str(completion)  # Last resort

        logger.info(f"OpenAI API - Full response dict: {response_dict}")
        logger.info(f"OpenAI API - Model used: {completion.model}")
        logger.info(f"OpenAI API - Usage info: {completion.usage}")
        logger.info(f"OpenAI API - Response ID: {completion.id}")

        if not completion.choices:
            logger.error("OpenAI API returned no choices in response")
            raise ValueError("No content in OpenAI response")

        message = completion.choices[0].message
        logger.info("Message object details:")
        logger.info(f"- Role: {message.role}")
        logger.info(f"- Content: {message.content}")
        logger.info(f"- Has tool_calls: {message.tool_calls is not None}")
        logger.info(f"- Has function_call: {message.function_call is not None}")
        logger.info(f"- Has refusal: {getattr(message, 'refusal', None) is not None}")

        # Special handling for o1-preview
        if "o1" in model_config["model"]:
            # Check for refusal
            refusal = getattr(message, "refusal", None)
            if refusal:
                logger.warning(f"O1 model refused to respond: {refusal}")
                raise ValueError(f"O1 model refused to respond: {refusal}")

            if message.tool_calls:
                logger.info("Response contained tool_calls instead of content")

            if message.function_call:
                logger.info("Response contained function_call instead of content")

        response_content = message.content
        if not response_content:
            logger.error("OpenAI API returned empty content")
            logger.error(f"Full message object for empty content: {message}")

            if "o1" in model_config["model"]:
                logger.error("This was an o1-preview request. Request details:")
                logger.error(
                    f"System content length: {len(system_content) if system_content else 0}"
                )
                logger.error(
                    f"User content length: {len(user_content) if user_content else 0}"
                )
            raise ValueError("Empty content in OpenAI response")

        logger.info(f"OpenAI API response first 500 chars: {response_content[:500]}...")
        return response_content

    except asyncio.TimeoutError:
        logger.error("OpenAI API call timed out")
        raise
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        logger.exception("Full traceback from call_openai:")
        raise
