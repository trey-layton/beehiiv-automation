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
- sections that contain links or references to external resources that add value or relevant context

Exclude sections that are not suitable for content generation, such as:
- Sponsored content or advertisements.
- Calls to action, subscription prompts, or promotional material.
- Headers, footers, disclaimers, or other boilerplate text.
- Social media links, contact information, or unsubscribe instructions.
- Repeat sections
- Sections too short to generate a thread on.
- Sections with links that are purely promotional or irrelevant to the main topic.

When making your posts, prioritize richer sections with adequate content. So rather than include just the title section or a fun "what I'm listening to", choose sections with more density of valuable information. 

However, do not automatically discard a section just because it primarily includes links. If the links themselves provide useful resources, context, or interesting reading material, treat that section as valuable content. (e.g., a “Weekly Links” or “Further Reading” section can be its own post if it directs readers to relevant resources.)

Again, I need you to provide the ENTIRE section as it is passed to you. Do not cut any of it off or summarize it in any way, including urls, links, image placeholders, and other formatting that was originally included.

Be mindful of media/asset placeholders ([image: url: "www.site.com....]). We need these downstream, so ALWAYS INCLUDE them in your output, leaving them in exactly the same place as they were located.

Format your response exactly as follows:
~![
    {"post_number": 1, "section_title": "main_story", "section_content": "Full content..."},
    {"post_number": 2, "section_title": "job_postings", "section_content": "Full content..."}
]!~

Do not include any additional text or formatting beyond what's inside the array.""",
    }

    user_message = {
        "role": "user",
        "content": f"{newsletter_structure}",
    }

    try:
        response = await call_language_model(system_message, user_message, "high")
        logger.info(f"Raw response from AI assistant: {response}")

        # Extract content between delimiters
        match = re.search(r"~!(.*?)!~", response, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            logger.debug(f"Extracted content: {extracted_content}")

            # Remove any problematic control chars
            sanitized_content = re.sub(r"[\x00-\x1f\x7f]", "", extracted_content)
            logger.debug(f"Sanitized content: {sanitized_content}")

            try:
                parsed_response = json.loads(sanitized_content)
                if isinstance(parsed_response, list):
                    return json.dumps(parsed_response, indent=2)
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
        return json.dumps([])
