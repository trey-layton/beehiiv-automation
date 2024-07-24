import logging
import re
from core.content.text_utils import clean_text, truncate_text
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def generate_pre_cta_thread(text, api_key, example_post):
    logger.info("Generating pre-newsletter CTA Thread post")
    try:
        system_message = {
            "role": "system",
            "content": "You are a skilled social media copywriter creating an engaging pre-newsletter CTA Thread post for a top creator. Generate a single post of maximum 500 characters that intrigues readers about the upcoming newsletter. The post should be catchy and encourage people to subscribe. Return ONLY the post content, no additional text.",
        }
        user_message = {
            "role": "user",
            "content": f"Create a pre-newsletter CTA Thread post based on this newsletter content. Emulate this style: '{example_post}'\n\nNewsletter content:\n{text}",
        }

        response_content = await call_language_model(
            api_key, system_message, user_message
        )
        logger.info(f"Language model response: {response_content}")

        if isinstance(response_content, dict):
            post = response_content.get("text", "")
        elif isinstance(response_content, str):
            post = response_content
        else:
            post = ""

        cleaned_post = clean_text(post.strip())
        truncated_post = truncate_text(cleaned_post, max_length=500)

        logger.info(f"Generated pre-CTA Thread post: {truncated_post}")
        return truncated_post

    except Exception as e:
        logger.exception(f"Error in generate_pre_cta_thread: {str(e)}")
        return ""


async def generate_post_cta_thread(text, api_key, example_post):
    logger.info("Generating post-newsletter CTA Thread post")
    try:
        system_message = {
            "role": "system",
            "content": "You are a skilled social media copywriter creating an engaging post-newsletter CTA Thread post for a top creator. Generate a single post of maximum 500 characters that summarizes the key points of the newsletter and encourages readers to check out the full content. Return ONLY the post content, no additional text.",
        }
        user_message = {
            "role": "user",
            "content": f"Create a post-newsletter CTA Thread post based on this newsletter content. Emulate this style: '{example_post}'\n\nNewsletter content:\n{text}",
        }

        response_content = await call_language_model(
            api_key, system_message, user_message
        )
        logger.info(f"Language model response: {response_content}")

        if isinstance(response_content, dict):
            post = response_content.get("text", "")
        elif isinstance(response_content, str):
            post = response_content
        else:
            post = ""

        cleaned_post = clean_text(post.strip())
        truncated_post = truncate_text(cleaned_post, max_length=500)

        logger.info(f"Generated post-CTA Thread post: {truncated_post}")
        return truncated_post

    except Exception as e:
        logger.exception(f"Error in generate_post_cta_thread: {str(e)}")
        return ""


async def generate_thread_posts(text, api_key, example_post):
    logger.info("Generating Thread posts")
    try:
        system_message = {
            "role": "system",
            "content": "You are a skilled social media copywriter creating engaging Thread posts for a top creator. Generate a list of 5 posts summarizing the main takeaways from the newsletter. Each post must be a maximum of 500 characters. Focus on one key point or insight per post, and don't include any extra information. Return your answer as a JSON object with numbered keys (1., 2., 3., 4., 5.) for each post. Ensure each post has a strong, punchy hook that keeps the reader engaged and motivated to move to the next post in the order. Make sure it sounds natural and flows well as a complete piece. Only focus on the most important, big-picture lessons or takeaways from the newsletter. Return ONLY the document, no intro or conclusion text.",
        }
        user_message = {
            "role": "user",
            "content": f"Create Thread posts based on this newsletter content. Emulate this style: '{example_post}'\n\nNewsletter content:\n{text}",
        }

        response_content = await call_language_model(
            api_key, system_message, user_message
        )
        logger.info(f"Language model response: {response_content}")

        posts = []
        if isinstance(response_content, dict) and "text" in response_content:
            response_text = response_content["text"]
            post_pattern = r"\d+\.\s*(.+?)(?=\n\d+\.|\Z)"
            posts = [
                match.group(1).strip()
                for match in re.finditer(post_pattern, response_text, re.DOTALL)
            ]
        elif isinstance(response_content, dict):
            posts = [
                post.strip() for key, post in response_content.items() if key.isdigit()
            ]

        cleaned_posts = [clean_text(post.strip()) for post in posts]
        truncated_posts = [
            truncate_text(post, max_length=500) for post in cleaned_posts
        ]

        logger.info(f"Generated {len(truncated_posts)} Thread posts: {truncated_posts}")
        return truncated_posts

    except Exception as e:
        logger.exception(f"Error in generate_thread_posts: {str(e)}")
        return []
