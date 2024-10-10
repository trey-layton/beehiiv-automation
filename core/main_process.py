import json
import logging
import re
from typing import Dict, Any, List
from supabase import Client as SupabaseClient
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.llm_steps.structure_analysis import analyze_structure
from core.llm_steps.content_strategy import determine_content_strategy
from core.llm_steps.content_generator import generate_content

logger = logging.getLogger(__name__)


def clean_and_validate_json(response: str) -> dict:
    try:
        logger.info(f"Raw response for cleaning: {response[:100]}...")
        # Remove any text before the actual JSON starts (if LLM adds text)
        cleaned_response = re.search(r"(\{.*\}|\[.*\])", response, re.DOTALL).group(0)
        logger.info(f"Cleaned JSON string: {cleaned_response[:100]}...")
        # Attempt to parse the cleaned response as JSON
        parsed_response = json.loads(cleaned_response)
        logger.info(f"Parsed JSON response: {parsed_response}")
        return parsed_response
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Failed to clean and parse LLM response: {str(e)}")
        return {"error": "Malformed response"}


def process_post_content(post_content: dict, post_number: int) -> dict:
    """
    Process and structure the content for each post, ensuring that it follows the expected format.
    """
    logger.info(f"Processing post number {post_number}, post content: {post_content}")

    formatted_posts = []
    if "content_container" in post_content and isinstance(
        post_content["content_container"], list
    ):
        for post in post_content["content_container"]:
            if isinstance(post, dict) and "content_container" in post:
                for sub_post in post["content_container"]:
                    post_type = sub_post.get("post_type", "")
                    post_text = sub_post.get("content_text", "")

                    if isinstance(post_text, str):
                        formatted_posts.append(
                            {"post_type": post_type, "content_text": post_text.strip()}
                        )
                    else:
                        logger.error(
                            f"Invalid post content type: {type(post_text)}. Converting to string."
                        )
                        formatted_posts.append(
                            {
                                "post_type": post_type,
                                "content_text": str(post_text).strip(),
                            }
                        )
            else:
                logger.error(f"Invalid post structure: {post}")

        return {"post_number": post_number, "post_content": formatted_posts}

    logger.error(
        f"Invalid post structure for post number {post_number}: {post_content}"
    )
    return {"error": "Invalid post structure", "post_number": post_number}


async def run_main_process(
    account_profile: AccountProfile,
    post_id: str,
    content_type: str,
    supabase: SupabaseClient,
) -> Dict[str, Any]:
    try:
        # Step 1: Fetch the content from the newsletter source (beehiiv)
        logger.info(f"Fetching content for post_id: {post_id}")
        content_data = await fetch_beehiiv_content(account_profile, post_id, supabase)
        logger.info(f"Fetched content data: {content_data}")

        original_content = content_data.get("free_content")
        web_url = content_data.get("web_url")
        thumbnail_url = content_data.get("thumbnail_url")

        logger.info(f"Original content: {original_content[:100]}...")
        logger.info(f"web_url: {web_url}, thumbnail_url: {thumbnail_url}")

        # Step 2: Analyze the structure of the content
        logger.info("Analyzing content structure...")
        newsletter_structure: str = await analyze_structure(original_content)
        logger.info(f"Newsletter structure: {newsletter_structure[:100]}...")

        # Step 3: Determine the content strategy
        logger.info("Determining content strategy...")
        content_strategy: str = await determine_content_strategy(newsletter_structure)
        logger.info(f"Content strategy: {content_strategy[:100]}...")

        # Step 4: Parse the content strategy
        try:
            strategy_list = json.loads(content_strategy)
            logger.info(f"Parsed content strategy: {strategy_list}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse content strategy JSON: {str(e)}")
            return {"error": "Failed to parse content strategy", "success": False}

        # Step 5: Process each section of the content strategy
        generated_contents: List[dict] = []

        for strategy in strategy_list:
            post_number = strategy.get("post_number", "unknown")
            logger.info(f"Processing post number {post_number}...")

            try:
                post_content = await generate_content(
                    strategy, content_type, account_profile, web_url, post_number
                )
                logger.info(f"Generated content for post {post_number}: {post_content}")

                # Process the post content into the desired structure
                formatted_post = process_post_content(post_content, post_number)
                if "error" in formatted_post:
                    return {"error": formatted_post["error"], "success": False}

                generated_contents.append(formatted_post)

            except Exception as e:
                logger.error(
                    f"Error generating content for post {post_number}: {str(e)}"
                )
                return {"error": str(e), "success": False}

        # Step 6: Construct the final payload
        logger.info("Constructing final payload...")
        final_content = {
            "provider": "twitter" if "tweet" in content_type else "linkedin",
            "type": content_type,
            "content": generated_contents,
            "thumbnail_url": thumbnail_url,
            "metadata": {"web_url": web_url, "post_id": post_id},
            "success": True,
        }

        logger.info(f"Final content payload: {final_content}")
        return final_content

    except Exception as e:
        logger.error(f"Error in run_main_process for post_id {post_id}: {str(e)}")
        return {"error": str(e), "success": False}
