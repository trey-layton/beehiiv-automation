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
        "content": """You are an expert content strategist specializing in repurposing newsletter content for social media. You will be passed a full newsletter deconstructed into its individual sections. Your task is to:

There should be a minimum of 1 post and maximum of 5 posts per newsletter, but really just use your best judgement to determine how many posts to make based on how valuable and rich the content is. Follow these guidelines:

Select Appropriate Sections:
Include sections that contain valuable content such as 
- news stories
- articles
- tips
- guides
- tutorials
- or any informative material suitable for content generation
Exclude sections that are not suitable for content generation, such as:
- Sponsored content or advertisements.
- Calls to action, subscription prompts, or promotional material.
- Headers, footers, disclaimers, or other boilerplate text.
- Social media links, contact information, or unsubscribe instructions.
- Repeat sections
- Sections too short to generate a thread on.

When making your posts, prioritize richer sections with adequate content. So rather than include just the title section or a fun "what I'm listening to", choose sections with more density of valuable information.

Again, I need you to provide the ENTIRE section as it is passed to you. Do not cut any of it off or summarize it in any way.

Format your response exactly as follows:
[
    {"post_number": 1, "section_title": "main_story", "section_content": "Full content..."},
    {"post_number": 2, "section_title": "job_postings", "section_content": "Full content..."}
]

Do not include any additional text or formatting beyond what's inside the array.""",
    }

    # Define the user message with the provided newsletter structure
    user_message = {
        "role": "user",
        "content": f"{newsletter_structure}",
    }
    try:
        # Call the language model
        response = await call_language_model(system_message, user_message, "high")

        # Extract content between delimiters
        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            logger.debug(f"Extracted content: {extracted_content}")

            # Sanitize the extracted content
            sanitized_content = re.sub(r"[\x00-\x1f\x7f]", "", extracted_content)
            logger.debug(f"Sanitized content: {sanitized_content}")

            try:
                # Parse and return the content as a list of sections
                parsed_response = json.loads(sanitized_content)
                if isinstance(parsed_response, list):
                    return json.dumps(
                        parsed_response, indent=2
                    )  # Return the clean array
                else:
                    logger.warning(
                        "Parsed content is not a list. Returning empty list."
                    )
                    return json.dumps([])
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse extracted content as JSON: {e.msg} at line {e.lineno} column {e.colno} (char {e.pos})"
                )
                return json.dumps([])
        else:
            logger.warning("No content found between delimiters. Returning empty list.")
            return json.dumps([])
    except Exception as e:
        logger.error(f"Error during content strategy processing: {str(e)}")
        # Return an empty list to maintain consistent return type
        return json.dumps([])
