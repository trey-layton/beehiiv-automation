# core/content/content_editor.py

import logging
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def edit_content(content: str, content_type: str) -> str:
    logger.info(f"Editing {content_type} content")

    system_message = {
        "role": "system",
        "content": """You are an expert social media copywriter specializing in creating engaging, natural-sounding posts. Your task is to improve the given post by:
- First, determine if this is a tweet or not. If it's <280 characters, it's a tweet, so make sure that the revised version you generate is also shorter than 280 characters.
- Improving the hook by keeping it to 8 words max, and make it something bold (emulate Mr. Beast... massive numbers, "how to", bold statements followed by sentences that start with "but" and contradict the first sentence, etc)... really cater this to what makes the most sense for this specific post
- Adding smooth transitions between tweets so that it sounds like a single, coherent narrative
- Avoiding phrases commonly associated with AI-generated content ("revolutionizing", "landscape is shifting", "paradise", "rollercoaster", "dive in", "shifting dynamics", "breakthroughs")
- Getting rid of fragments and choppy points which seem incoherent or unnatural. The final should be concise, but NEVER CHOPPY.
- Avoiding too many colons to start tweets (come off as AI-generated)
- Maintain the core message, details, and key points of each post while making these improvements. 
- Make sure the hook stays strong.
If it is a Twitter Thread, keep it as a Twitter thread and make sure each individual tweet complies with limits.
If the post was already under 280 characters, keep the revised and edited one under this length as well.
If it is a long-form post, keep the same length.
Critical note: keep the exact same plain text structure that you received the post in. (single for long-form, multiple objects for threads, etc). EXACTLY THE SAME STRUCTURE. Do not add any extra fields or change the structure. 
And do not include any intro or filler text beyond the actual post content. This gives you a few more characters in each individual post. Just get straight into the post content
DO NOT USE line break characters
Again, if the original post was under 280 character, THIS ONE HAS TO BE UNDER 280 ALSO. MAKE SURE TO DOUBLE CHECK THIS CHARACTER COUNT AND REVISE IF YOU NEED TO""",
    }

    user_message = {
        "role": "user",
        "content": f"Please review and improve the following {content}",
    }

    try:
        edited_content = await call_language_model(system_message, user_message)
        logger.info(f"Content editing completed for {content_type}")
        return edited_content
    except Exception as e:
        logger.error(f"Error in content editing: {str(e)}")
        raise
