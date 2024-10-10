import importlib
import logging
import re
import json
from typing import Dict, Any
from core.models.account_profile import AccountProfile
from core.utils.llm_response_handler import LLMResponseHandler
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)
from core.social_media.twitter import (
    precta_tweet,
    postcta_tweet,
    thread_tweet,
    long_form_tweet,
)
from core.social_media.linkedin import long_form_post

CONTENT_TYPE_MAP = {
    "precta_tweet": precta_tweet,
    "postcta_tweet": postcta_tweet,
    "thread_tweet": thread_tweet,
    "long_form_tweet": long_form_tweet,
    "linkedin_long_form_post": long_form_post,
}


def clean_llm_response(response: str) -> str:
    """
    Cleans and ensures that the LLM response is properly escaped
    for safe JSON parsing.
    """
    try:
        clean_response = json.loads(response)
        logger.info("Successfully parsed JSON response without modification.")
        return clean_response

    except json.JSONDecodeError:
        logger.error(f"Raw LLM Response: {response}")
        logger.error("JSON parsing failed. Attempting to clean the response.")
        match = re.search(r"(\{.*\}|\[.*\])", response, re.DOTALL)
        if match:
            try:
                cleaned_json_str = match.group(0)
                cleaned_json = json.loads(cleaned_json_str)
                logger.info(f"Manually cleaned and parsed response: {cleaned_json}")
                return cleaned_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse manually extracted content: {str(e)}")
                raise ValueError("Manually extracted content is not valid JSON.")
        else:
            raise ValueError("Unable to extract valid JSON from LLM response.")


def get_instructions_for_content_type(content_type: str) -> Dict[str, Any]:
    try:
        module = CONTENT_TYPE_MAP.get(content_type)
        if not module:
            raise ModuleNotFoundError(f"Content type '{content_type}' not found.")
        return module.instructions

    except ModuleNotFoundError as e:
        logging.error(f"Error fetching instructions for {content_type}: {e}")
        return {"content_generation": ""}


def escape_special_characters(text: str) -> str:
    try:
        return json.dumps(text)[1:-1]  # [1:-1] to remove extra quotes added by dumps
    except Exception as e:
        logger.error(f"Failed to escape special characters: {str(e)}")
        return text  # Fallback to original text in case of failure


async def generate_content(
    strategy: Dict[str, Any],
    content_type: str,
    account_profile: AccountProfile,
    web_url: str,
    post_number: int,
    instructions: Dict[str, Any] = None,
) -> Dict[str, Any]:
    logger.info(
        f"Starting content generation for: {content_type}, post number: {post_number}"
    )

    if instructions is None:
        instructions = get_instructions_for_content_type(content_type)

    content_generation_instructions = instructions.get("content_generation", "")
    system_message = {
        "role": "system",
        "content": f"""
        You are an AI assistant specializing in creating engaging social media content.
        Your task is to generate a {content_type} based on the provided newsletter section.
        Follow these guidelines:
        1. Maintain the original meaning and key information from the source content.
        2. Adapt the style to suit the {content_type} format and the account's preferences.
        3. Ensure the content is engaging and suited for the target platform.
        4. {content_generation_instructions}
        
        Format your response as a JSON object with 'type' and 'content' keys. The 'content' should be a list of post objects.
        """,
    }

    user_message = {
        "role": "user",
        "content": f"""
        Generate a {content_type} based on this newsletter section:
        Content: {strategy}
        Account preferences: {account_profile.json()}
        Original content URL: {web_url}
        """,
    }

    try:
        # Call the language model and get the raw response
        response = await call_language_model(system_message, user_message)
        logger.info(f"Full Raw LLM response: {response}")

        try:
            response_json = json.loads(response)
            logger.info("Parsed JSON successfully.")
        except json.JSONDecodeError:
            logger.error(
                "Failed to parse JSON normally, attempting to clean the response."
            )
            response_json = clean_llm_response(response)

        if "content_container" not in response_json or not isinstance(
            response_json["content_container"], list
        ):
            logger.error(f"Invalid response format: {response_json}")
            return {"error": "Invalid response format", "success": False}

        # Step 4: Extract formatted posts
        formatted_posts = []
        logger.info(f"Response JSON content_container: {response_json}")

        for post in response_json["content_container"]:
            post_type = post.get("post_type", "")
            post_content = post.get(
                "post_content", ""
            )  # Update key to post_content as per the raw LLM response

            logger.info(
                f"Processing post number {post_number}, type: {post_type}, post content: {post_content}"
            )
            logger.info(f"Post content type: {type(post_content)}")

            if isinstance(post_content, str):
                logger.info(
                    f"Post content is a string. Wrapping it in a list: {post_content}"
                )
                post_content = [post_content]  # Convert to list to maintain consistency
            elif isinstance(post_content, list):
                logger.info(f"Post content is already a list: {post_content}")
            else:
                logger.error(f"Unexpected type for post_content: {type(post_content)}")

            if isinstance(post_content, list):
                sub_posts = []
                for sub_post in post_content:
                    logger.info(
                        f"Processing sub_post: {sub_post}, sub_post type: {type(sub_post)}"
                    )

                    if isinstance(sub_post, dict):
                        logger.info(
                            f"Sub-post is a valid dict. Adding to sub_posts: {sub_post}"
                        )
                        sub_posts.append(sub_post)
                    elif isinstance(sub_post, str):
                        logger.info(
                            f"Sub-post is a string. Converting to JSON object with type {post_type}"
                        )
                        sub_posts.append(
                            {"post_type": post_type, "content_text": sub_post.strip()}
                        )
                    else:
                        logger.error(
                            f"Unexpected sub-post type: {type(sub_post)}. Converting to string."
                        )
                        sub_posts.append(
                            {
                                "post_type": post_type,
                                "content_text": str(sub_post).strip(),
                            }
                        )

                formatted_posts.append(
                    {
                        "content_type": post_type,
                        "content_container": sub_posts,  # Add the array of sub-posts for this main post
                    }
                )
                logger.info(f"Formatted post: {formatted_posts[-1]}")
            else:
                logger.error(f"Unexpected content type for post: {type(post_content)}")
                post_content = [str(post_content)]
                formatted_posts.append(
                    {"content_type": post_type, "content_container": post_content}
                )
                logger.info(
                    f"Added post with unexpected content type: {formatted_posts[-1]}"
                )

        logger.info(
            f"Extracted {len(formatted_posts)} posts for post number {post_number}"
        )
        return {
            "post_number": post_number,
            "content_container": formatted_posts,
        }

    except Exception as e:
        logger.error(f"Error during content generation: {e}")
        return {"error": str(e), "success": False}
