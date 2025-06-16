"""
Newsletter Structure Analysis Module - Step 1 of AI Processing Pipeline.

This module implements the first critical step in the PostOnce AI pipeline:
intelligent analysis and sectioning of newsletter content. Using advanced
reasoning models, it breaks down complex newsletter content into logical,
processable sections for optimal social media content generation.

Key Features:
- AI-powered content structure recognition
- Intelligent section identification and categorization
- JSON-structured output for downstream processing
- Robust parsing with fallback mechanisms
- Advertisement and promotional content filtering

The module processes raw newsletter content and produces a structured JSON
output that identifies distinct content sections, enabling the content strategy
module to plan optimal social media distribution strategies.

Processing Flow:
1. **Content Analysis**: AI examines newsletter structure and themes
2. **Section Identification**: Identifies logical content boundaries
3. **Content Categorization**: Classifies sections (main story, headlines, etc.)
4. **Promotional Filtering**: Removes ads and non-core content
5. **JSON Structuring**: Outputs structured data for next pipeline step

Output Format:
The module produces JSON with this structure:
```json
{
    "sections": [
        {
            "section_title": "Main Story",
            "section_content": "Full content of the main article..."
        },
        {
            "section_title": "Headlines",
            "section_content": "Brief news items and updates..."
        }
    ]
}
```

Usage in Pipeline:
This is the first step in the 7-step AI pipeline, feeding into content
strategy determination. The structured output enables intelligent content
distribution planning across multiple social media posts.

Example:
    newsletter_structure = await analyze_structure(raw_newsletter_content)
    # Returns structured JSON ready for strategy determination
"""

import json
import logging
import re
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def analyze_structure(content: str) -> str:
    """
    Analyze newsletter content structure using AI reasoning models.

    This function uses advanced AI models (specifically OpenAI's o1-preview)
    to intelligently analyze newsletter content and break it into logical
    sections for optimal social media content generation.

    The AI performs sophisticated content analysis to:
    - Identify main stories vs. secondary content
    - Group related short articles into meaningful sections
    - Filter out promotional and non-core content
    - Create descriptive section titles
    - Preserve all essential content while removing noise

    Args:
        content: Raw newsletter content (HTML-cleaned but with structure preserved)

    Returns:
        JSON string containing structured sections in the format:
        ```json
        {
            "sections": [
                {
                    "section_title": "Descriptive section name",
                    "section_content": "Full content for this section"
                }
            ]
        }
        ```

    Raises:
        Exception: If AI processing fails or content cannot be parsed

    Processing Details:
        - Uses 'o1' tier model for advanced reasoning capabilities
        - Removes promotional content (ads, sponsorships, CTAs)
        - Excludes boilerplate content (headers, footers, welcome messages)
        - Preserves image placeholders and URLs for downstream processing
        - Handles edge cases like interrupted content and mixed formats

    Content Sectioning Logic:
        - Single coherent pieces → One section
        - Multiple distinct topics → Multiple sections by theme
        - Featured stories → Dedicated sections even if mentioned elsewhere
        - Short articles → Grouped into collective sections (e.g., "Headlines")
        - Mixed content → Intelligently categorized and separated

    Example:
        ```python
        newsletter_html = '''
        <h1>Weekly Update</h1>
        <h2>Major Industry Changes</h2>
        <p>Details about major changes...</p>
        <h2>Quick Headlines</h2>
        <ul><li>Brief update 1</li><li>Brief update 2</li></ul>
        '''

        structure = await analyze_structure(newsletter_html)
        # Returns JSON with "Major Industry Changes" and "Quick Headlines" sections
        ```

    Note:
        This is Step 1 of the 7-step AI pipeline. The structured output
        feeds directly into content strategy determination (Step 2).
    """
    system_message = {
        "role": "system",
        "content": """You are an AI assistant specialized in breaking down newsletters into logical sections. Your goal is to output these sections as valid JSON, following these rules:

1. **Sectioning Rules**  
   - If the newsletter is essentially a single coherent piece (e.g., an essay), create only one section.  
   - If there are multiple topics or articles, divide them into multiple sections based on **content** (e.g., "Main Story," "Headlines," "Job Postings," "Courses," "Events," etc.).  
   - If the newsletter has a featured or "main" story, create a dedicated section for it **even if** it also appears in a broader "Headlines" list.  
   - When there are several short articles (none big enough to stand alone), group them together under a single section, such as "Headlines" or "Secondary Stories."

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
   - Each section object's **section_title** is a brief, descriptive header (e.g., "Main Story," "Headlines," "Job Postings").  
   - Each section object's **section_content** must contain the **full, unmodified content** for that section, including URLs and placeholders (e.g., `[image: url: "www.site.com"]`).

3. **Excluding Non-Core Content**  
   - **Exclude** anything obviously promotional or sponsored—ads, discount codes, sponsor plugs, subscription links, etc.—from your final output.  
   - Also exclude intros or "welcome" messages, footers, sign-offs, or any boilerplate lines that are not part of the actual stories/content.  
   - If an advertisement interrupts the middle of real content, remove the ad but **preserve** the real content on both sides (don't accidentally split the section).

4. **Examples**  
   (Retain or shorten the existing examples to illustrate how you want main stories vs. secondary stories vs. single-article newsletters to be handled.)

5. **Edge Cases**  
   - If the main story also appears in a "Headlines" list, that's fine; you may show it in both.  
   - Always strive for **fewer, more meaningful sections**—don't artificially subdivide one coherent story.  
   - If in doubt whether something is an ad or core content, try to infer from context. Ads are typically sponsor mentions, product plugs, discount offers, or subscription promos.

**Output**  
Return the final JSON in **one line**, surrounded by `~!` and `!~`, with **no** additional commentary, explanation, or text.
""",
    }

    user_message = {
        "role": "user",
        "content": f"{content}",
    }
    response = await call_language_model(system_message, user_message, "o1")
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
