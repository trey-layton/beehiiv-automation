import re
import logging
from typing import Union, List, Dict
from core.content.language_model_client import call_language_model
from core.models.content import Content, Post

logger = logging.getLogger(__name__)


def parse_content(content: str) -> List[Dict[str, str]]:
    # Split the content based on the *n* markers
    parts = re.split(r"\*\d+\*", content)

    # Remove any leading/trailing whitespace and empty parts
    parts = [part.strip() for part in parts if part.strip()]

    # Create a list of dictionaries
    result = []
    for i, part in enumerate(parts):
        if i == 0:
            result.append({"type": "main_tweet", "text": part})
        else:
            result.append({"type": "reply_tweet", "text": part})

    return result


async def edit_single_post(
    content: Union[str, list], content_type: str
) -> Union[str, list]:
    logger.info(f"Editing content for content_type: {content_type}")

    system_message = {
        "role": "system",
        "content": """You are an expert social media copywriter specializing in creating engaging, natural-sounding posts. Your task is to improve the given content based on its type:

1. For all content types:
   - Make the hook super catchy. Make it something bold and daring, throw a big number in, start with "How to" or something that will really make people stop and want to read on.
   - Avoid phrases commonly associated with AI-generated content such as "revolutionizing", "democratizing", "changing the game"
   - Maintain the core message and key points while improving clarity and engagement potential
   - Ensure the content flows naturally and is never choppy, both between subsequent individual posts as part of a larger post and within posts so as to avoid fragments

2. For pre-CTA, post-CTA, and thread tweets:
   - Respect the 280-character limit for individual tweets while making the group of posts more comprehensive and detailed.
   - For pre-CTA and post-CTA, ensure the main tweet and reply tweet (only two tweets) work together cohesively (the first tweet should never have a link, and the second tweet should be super short and primarily about the CTA to check out the link. Always include the provided link in the second tweet). The first tweet should contain the hook and the teaser content (don't just make it the hook, and don't add any additional detail beyond the link in the reply tweet)
   - For threads, maintain a logical flow between tweets, trying to strengthen the flow between them as much as you can. Also, make sure you preserve the tweet type (reply_tweet, quote_tweet, etc)

3. For LinkedIn posts:
   - Optimize for professional tone while maintaining engagement.
   - Structure the content for easy readability on the LinkedIn platform (line break between every sentence with an extra blank line between lines of text, use numbering and bullets)

4. For long-form content:
   - Break up large text blocks into more digestible sections (line break between every sentence with an extra blank line between lines of text)
   - Use formatting (like bullet points or numbered lists) where appropriate to improve readability.

Important: Mark the beginning of each tweet with *1*, *2*, etc. For example:

'*1* This is the main tweet content. It's engaging and within 280 characters.

*2* This is the first reply tweet. It continues the thought from the main tweet.'

Do not include any text except for the actual post content, so no intro text like 'Here's an improved version', etc""",
    }

    if isinstance(content, list):
        content_for_editing = "\n\n".join(
            [f"*{i+1}* {item['text']}" for i, item in enumerate(content)]
        )
    else:
        content_for_editing = f"*1* {content}"

    user_message = {
        "role": "user",
        "content": f"Please review and improve the following {content_type} content:\n\n{content_for_editing}",
    }

    try:
        edited_content = await call_language_model(
            system_message, user_message, tier="high"
        )
        logger.info(f"Raw edited content for {content_type}: {edited_content}")

        parsed_content = parse_content(edited_content)

        if not parsed_content:
            logger.warning(
                f"Failed to parse edited content for {content_type}. Returning original content."
            )
            return (
                content
                if isinstance(content, str)
                else [{"type": "post", "text": str(content)}]
            )

        return parsed_content

    except Exception as e:
        logger.error(f"Error in content editing: {str(e)}")
        return (
            content
            if isinstance(content, str)
            else [{"type": "post", "text": str(content)}]
        )
        return parsed_content

    except Exception as e:
        logger.error(f"Error in content editing: {str(e)}")
        return (
            content
            if isinstance(content, list)
            else [{"type": "post", "text": content}]
        )


async def edit_content(content: Content, content_type: str) -> Content:
    logger.info(f"Editing content for content_type: {content_type}")
    edited_posts = []

    for post in content.posts:
        try:
            edited_content = await edit_single_post(post.content, content_type)

            # Check if edited_content is a list (multiple posts) or a single string
            if isinstance(edited_content, list):
                for i, item in enumerate(edited_content):
                    edited_posts.append(
                        Post(
                            post_number=post.post_number + i,
                            section_type=post.section_type,
                            content=item["text"],
                            metadata=post.metadata,
                        )
                    )
            else:
                edited_posts.append(
                    Post(
                        post_number=post.post_number,
                        section_type=post.section_type,
                        content=edited_content,
                        metadata=post.metadata,
                    )
                )
        except Exception as e:
            logger.error(f"Error editing post {post.post_number}: {str(e)}")
            logger.exception("Traceback:")
            # If editing fails, keep the original content
            edited_posts.append(post)

    return Content(
        segments=content.segments,
        strategy=content.strategy,
        posts=edited_posts,
        original_content=content.original_content,
        content_type=content.content_type,
        account_id=content.account_id,
        metadata=content.metadata,
    )
