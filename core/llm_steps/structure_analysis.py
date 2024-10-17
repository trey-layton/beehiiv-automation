import json
import logging
import re
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)


async def analyze_structure(content: str) -> str:
    # logger.info("Starting structure analysis")

    # Define the system message to instruct the LLM
    system_message = {
        "role": "system",
        "content": """You are an advanced content structure analyzer specializing in newsletters. Your task is to break down newsletter content into logical segments without altering or summarizing the content. Follow these guidelines:

1. Identify distinct sections within the newsletter. 
2. Label each segment with a descriptive "type" that reflects its content or function.
3. Include the full, unaltered text of each segment.
4. Do not summarize, paraphrase, or modify the content in any way.
5. Avoid creating arbitrary divisions where the content flows as a cohesive unit.
6. Be aware of formatting cues, headings, and changes in writing style that might indicate segment breaks.
7. Recognize common newsletter elements such as introductions, main stories, conclusions, etc.
8. Do not include intros, headers, footers, or sponsored content in your output. These are the only sections you're allowed to leave out, and you should simply not include them in your json output.

I cannot stress enough how important it is for you to return the entire content of the newsletter. Do not cut sections off or try to summarize them.

Your job is to return a JSON object with clearly defined sections and titles from the newsletter provided. These should be the only content in your final response. The JSON should have the following format:
    
~!{
  "Section Title 1": "Full content of section 1",
  "Section Title 2": "Full content of section 2",
  ...
}!~
Use these delimiters (~! and !~) as the rest of the code depends on their inclusion for processing. 
Do not return anything other than valid JSON. Get rid of header, sponsored, and footer sections. Simply remove them from your final object before returning it.""",
    }

    user_message = {
        "role": "user",
        "content": f"Analyze the structure of the following newsletter content:\n\n{content}",
    }
    response = await call_language_model(system_message, user_message, "medium")

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
