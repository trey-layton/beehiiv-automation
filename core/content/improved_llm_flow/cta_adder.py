import logging
from typing import Dict, Any, Union, List
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)

CTA_INSTRUCTIONS = {
    "precta_tweet": "Encourage users to subscribe to the newsletter (this is a teaser post trying to get readers to subscirbe to the newsletter to get the newsletter when it goes out, but the article is now live yet) and link the subscribe link.",
    "postcta_tweet": "Encourage users to read the full article (which was just published) and link the edition link.",
    "thread_tweet": "Add a CTA to the second to last tweet encouraging users to read the full article (so link the full edition), and then in the last tweet, it's a quote tweet of the first tweet in the article encouraging readers to share and like it.",
    "long_form_tweet": "Add a CTA at the end, encouraging users to read the full article with the link to the full article.",
}


async def add_cta(
    content: Union[str, List[Dict[str, str]]],
    content_type: str,
    user_config: Dict[str, Any],
    edition_url: str,
) -> str:
    system_message = {
        "role": "system",
        "content": """You are an expert in creating engaging call-to-actions (CTAs) for social media posts that really get people to act. Your task is to add an appropriate CTA to the given content based on its type. Each has to adhere to the content length limits (280 characters for tweets). All of them are posted as replies to the main content to avoid the link penalty on social media posts. Use the following guidelines:
        {CTA_INSTRUCTIONS[content_type]}
        Ensure the CTA is concise, engaging, and fits naturally with the content. Avoid overused terms like 'dive in'""",
    }

    user_message = {
        "role": "user",
        "content": f"Add an appropriate CTA reply to this {content_type} content. Subscribe URL: {user_config['subscribe_url']}. Edition URL: {edition_url}. Content: {content} but DO NOT (and I repeat, DO NOT) make any changes to the existing content. Only add the reply post with the CTA.",
    }

    try:
        response = await call_language_model(system_message, user_message)

        # The response is now a string, not a dictionary
        return response.strip()

    except Exception as e:
        logger.exception(f"Error in add_cta: {str(e)}")
        return content
