import json
import logging
import re
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def analyze_structure(content: str) -> str:
    system_instructions = {
        "role": "system",
        "content": """You are an AI assistant specialized in breaking down newsletters into logical sections. Your goal is to output these sections as valid JSON, following these rules:

1. **Sectioning Rules**  
   - If the newsletter is essentially a single coherent piece (e.g., an essay), create only one section.  
   - If there are multiple topics or articles, divide them into multiple sections based on **content** (e.g., “Main Story,” “Headlines,” “Job Postings,” “Courses,” “Events,” etc.).  
   - If the newsletter has a featured or “main” story, create a dedicated section for it **even if** it also appears in a broader “Headlines” list.  
   - When there are several short articles (none big enough to stand alone), group them together under a single section, such as “Headlines” or “Secondary Stories.”

2. **Format**  
   - Output the final JSON on **one line**, wrapped between `~!` at the start and `!~` at the end, with no line breaks.  
   - The JSON must have the structure:
     ```
     {"sections":[
       {
         "section_title":"...",
         "section_content":"..."
       },
       {
         "section_title":"...",
         "section_content":"..."
       }
       ...
     ]}
     ```
   - Each section object’s **section_title** is a brief, descriptive header (e.g., “Main Story,” “Headlines,” “Job Postings”).  
   - Each section object’s **section_content** must contain the **full, unmodified content** for that section, including URLs and placeholders (e.g., `[image: url: "www.site.com"]`).

3. **Excluding Non-Core Content**  
   - **Exclude** anything obviously promotional or sponsored—ads, discount codes, sponsor plugs, subscription links, etc.—from your final output.  
   - Also exclude intros or “welcome” messages, footers, sign-offs, or any boilerplate lines that are not part of the actual stories/content.  
   - If an advertisement interrupts the middle of real content, remove the ad but **preserve** the real content on both sides (don’t accidentally split the section).

4. **Examples**  
   (Retain or shorten the existing examples to illustrate how you want main stories vs. secondary stories vs. single-article newsletters to be handled.)

5. **Edge Cases**  
   - If the main story also appears in a “Headlines” list, that’s fine; you may show it in both.  
   - Always strive for **fewer, more meaningful sections**—don’t artificially subdivide one coherent story.  
   - If in doubt whether something is an ad or core content, try to infer from context. Ads are typically sponsor mentions, product plugs, discount offers, or subscription promos.

Be mindful of media/asset placeholders ([image: url: "www.site.com....]). We need these downstream, so ALWAYS INCLUDE them in your output, leaving them in exactly the same place as they were located.

Format your response exactly as follows:
~![
    {"post_number": 1, "section_title": "main_story", "section_content": "Full content..."},
    {"post_number": 2, "section_title": "job_postings", "section_content": "Full content..."}
]!~

Do not include any additional text or formatting beyond what's inside the array.
""",
    }

    user_message = {
        "role": "user",
        "content": f"{system_instructions}\n\n{content}",
    }

    response = await call_language_model(
        {}, user_message, "o1-preview", provider_override="openai"
    )

    logger.info(f"Raw response from AI assistant: {response}")

    # Extract JSON content between delimiters
    match = re.search(r"~!\s*(.*?)\s*!~", response, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            parsed_response = json.loads(json_str)
            return json.dumps(parsed_response, indent=2)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extracted content as JSON: {e}")
    else:
        logger.error("Failed to find response between delimiters")

    # Fallback: Pass the raw response to the next step if parsing fails
    logger.warning("Falling back to passing the raw LLM response to the next step")
    return response
