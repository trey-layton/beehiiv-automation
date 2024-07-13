import logging
import re
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def generate_linkedin_post(text, api_key, example_post):
    logger.info("Generating LinkedIn post")
    logger.info(f"Content passed to language model (first 500 chars): {text[:500]}")
    try:
        system_message = {
            "role": "system",
            "content": "You are a skilled content creator specializing in LinkedIn posts. Generate a post of approximately 1000 characters that summarizes the main points of the given content. The post should be informative, engaging, and have a 'thought leadership' tone. Each sentence or key point should be on a new line, separated by <br>. Do not use emojis. The post should be ready to publish on LinkedIn. Do not include any additional text, formatting, or placeholders beyond the <br> separators.",
        }
        user_message = {
            "role": "user",
            "content": f"Create a LinkedIn post summarizing this newsletter content. Use a professional style similar to this example, but adapted for LinkedIn: {example_post}\n\nHere's the newsletter content:\n{text}",
        }

        response_content = await call_language_model(
            api_key, system_message, user_message
        )
        logger.info(f"Raw API response: {response_content}")

        # Extract post text from the response
        if isinstance(response_content, dict):
            post_text = (
                response_content.get("post") or response_content.get("text") or ""
            )
        elif isinstance(response_content, str):
            post_text = response_content
        else:
            logger.error(f"Unexpected response format: {response_content}")
            raise ValueError("Invalid response format from language model API")

        # Clean up the post text
        post_text = post_text.strip().strip('"')
        post_text = post_text.replace("\n", "<br>")
        post_text = post_text.replace("<br><br>", "<br>")
        post_text = re.sub(r"^(Post:?\s*)", "", post_text, flags=re.IGNORECASE)

        logger.info(f"Final LinkedIn post text (length {len(post_text)}):\n{post_text}")
        return post_text
    except Exception as e:
        logger.exception(f"Unexpected error in generate_linkedin_post: {str(e)}")
        raise
