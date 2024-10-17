import json
import logging
import re
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def determine_content_strategy(newsletter_structure: str) -> str:
    # Log the input newsletter structure (first 100 characters for brevity)
    # logger.info(f"Input newsletter structure: {newsletter_structure[:100]}...")
    system_message = {
        "role": "system",
        "content": """You are an expert content strategist specializing in repurposing newsletter content for social media. Your task is to analyze the structure and content of a newsletter and develop a strategic plan for social media posts. Follow these guidelines:

1. Assess the overall structure of the newsletter (single-section or multi-section).
2. For multi-section newsletters, create one post for each distinct section.
3. For single-section newsletters, create one main post covering the entire content and optionally 1-4 additional posts focusing on specific aspects.
4. Do not alter the original newsletter content.
5. Limit yourself to 5 posts maximum.
6. Do not create posts for introductions, sponsored content, or footers.
7. If there's no clear main story, treat secondary stories as a "top stories" section.
8. Never write about the intro, footer, or sponsored content. These should never ever be selected for posts.
For "single-section" newsletters (example: a list of reasons why coffee is good for you, or the entire newsletter is pretty much a personal anecdote), this should only be ONE section with only one post, so treat it as such.
For newsletters with various parts (like a few quick news stories, a jobs postings alert, an events tab, shorter secondary stories, etc), each of these sections should be its own section.
However, a main story can only count as a main story if it is noticeably longer than the other parts of the newsletter, not always just the first section of the newsletter... if they are all about the same length, this should be treated as a secondary post.

When making your posts, prioritize richer sections with adequate content. So rather than include just the title section or a fun "what I'm listening to", choose sections with more density of valuable information.

Again, I need you to provide the ENTIRE section as it is passed to you. Do not cut any of it off or summarize it in any way.

Format your response exactly as follows:
~!
[
    {"post_number": 1, "section_title": "main_story", "section_content": "Full content..."},
    {"post_number": 2, "section_title": "job_postings", "section_content": "Full content..."}
]
!~
Make sure to use these delimiters (~! and !~) to directly bracket the actual structured content as the rest of the code relies on this for parsing.
Do not include any additional text or formatting beyond what's inside the array.""",
    }

    # Define the user message with the provided newsletter structure
    user_message = {
        "role": "user",
        "content": f"Determine the content strategy for these newsletter sections:\n\n{newsletter_structure} Avoid suggesting multiple posts on the same topic.",
    }
    try:
        # Call the language model
        response = await call_language_model(system_message, user_message, "medium")

        # Extract content between delimiters
        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            try:
                # Parse and return the content as a list of sections
                parsed_response = json.loads(extracted_content)
                return json.dumps(parsed_response, indent=2)  # Return the clean array
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse extracted content as JSON. Returning empty list."
                )
                return json.dumps([])
        else:
            logger.warning("No content found between delimiters. Returning empty list.")
            return json.dumps([])
    except Exception as e:
        logger.error(f"Error during content strategy processing: {str(e)}")
        return json.dumps({"error": str(e)})
