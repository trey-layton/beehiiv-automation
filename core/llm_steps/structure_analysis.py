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
        "content": """You are an AI assistant specialized in processing newsletters. Your task is to break down newsletters into logical sections and output them as JSON objects. Follow these guidelines:

1. Divide the newsletter into coherent sections based on content, not formatting.
2. Create a JSON object for each section in the format {"descriptive_header":"full section content"}.
3. The descriptive_header should be a brief, content-based description of the section.
4. Include the full, unmodified content of each section.
5. Exclude titles, sponsored content, intros (like where the author breaks the 4th wall to welcome new subscribers or talks about what the newsletter is going to talk about), outros (like where the author thanks the subscriber, asks for feedback, etc), headers, footers, and any promotional or sponsored material that aren't core content.
6. If the newsletter is a single coherent piece (e.g., an essay), keep it as one section.
7. For newsletters with multiple topics, group related content together ("around the web", "main stories" (this applies if there is no clear, long, main story but rather several shorter ones), "job postings", "events board", "around the web", etc)
8. The number of sections should be dynamic and tailored to the newsletter's content.
9. Output the result as a single line starting with "~!" and ending with "!~", with no line breaks within this structure.

**Example Output Format:**

{"section_title": "descriptive_header", "section_content": "full section content"}

Example 1:

Input: "7 Common Psychological Manipulation Techniques You Face Every Day
Manipulation is something we all encounter in our daily lives. It often flies under the radar, masked in normal conversations, advertisements, or interactions with others. At its core, manipulation is the act of influencing someone’s thoughts, emotions, or actions for personal gain. When people use psychological manipulation, they are tapping into the intricacies of the human mind, making subtle moves that often go unnoticed but lead to powerful outcomes.
Understanding these techniques is crucial not only for protecting yourself but also for recognizing when you might be influenced in ways that aren’t aligned with your best interests. Below, we will explore some of the most common manipulation techniques used in everyday life.
Today's top surprising stories!
1. The Foot-in-the-Door Technique
One of the most common psychological manipulation techniques is the foot-in-the-door method… (continued for 6 more numbered paragraphs)
Checkout Recommendations!
5 Reasons We Love Wayfair
It's no secret that Wayfair provides a wide selection of home items at great prices. But why do we love it? Our deal experts at Brad’s Deals share their top 5 reasons.
Read more!
Suggested Readings
*   4 Important Messages Adults Need to Hear From Their Parents… (continued for 15 more bullets)
Update your email preferences or unsubscribe here
© 2024 Psychology Today XYZ
228 Park Ave S, #29976, New York, New York 10003, United States"

Output: "{"sections":[{"section_title":"Main Story","section_content":"7 Common Psychological Manipulation Techniques You Face Every Day. Manipulation is something we all encounter in our daily lives. It often flies under the radar, masked in normal conversations, advertisements, or interactions with others. At its core, manipulation is the act of influencing someone's thoughts, emotions, or actions for personal gain. When people use psychological manipulation, they are tapping into the intricacies of the human mind, making subtle moves that often go unnoticed but lead to powerful outcomes. Understanding these techniques is crucial not only for protecting yourself but also for recognizing when you might be influenced in ways that aren't aligned with your best interests. Below, we will explore some of the most common manipulation techniques used in everyday life. 1. The Foot-in-the-Door Technique. One of the most common psychological manipulation techniques is the foot-in-the-door method... (continued for 6 more numbered paragraphs)"},{"section_title":"Suggested Readings","section_content":"- 4 Important Messages Adults Need to Hear From Their Parents... (continued for 15 more bullets)"}]}"

Explanation: "This is a perfect example because it correctly identifies the main story and returns it in full (this example was cut off for demonstration purposes). It also correctly identifies the only other section with genuine content (the reading list) and returns it in full. It correctly chose not to include any titles, footers, or sponsored content like the randomly placed 5 reasons we love wayfare link. Note that this example used cut off content for demonstration purposes, but in production, always include the full content for that section."

Example 2:

Input: "Virginia Candidate Hosts Debate Against Incumbent’s AI Chatbot
Today’s Headlines:
*   Virginia Candidate Hosts Debate Against Incumbent’s AI Chatbot - Bentley Hensel, an independent congressional candidate in Virginia, has created an AI chatbot named DonBot to stand in for Democratic incumbent Don Beyer in a recent debate.
*   Elon Musk’s X Allows… (continued with 6 more one-sentence stories)
Got AI News to Share?
Have an AI news story or press release you'd like to share? Email Alicia@AiNews.com to get your news featured in our next edition!
AI In Action: Quick Tutorials
In this section, you'll find short, practical tutorials that walk you through using the latest AI tools, helping you quickly unlock their full potential.
Today’s AI in Action: Kling AI, one of the most popular AI video generators, now lets you add strategic movement to specific elements in AI video, providing more control in your generated clips.
Step-by-step:... (continues with implementation steps and tips)
AI Tools:
- ObjectRemover: Remove any object from your photos quickly and accurately with an AI-driven tool.
- EditApp: … (continues with several other AI tools)
Get in touch with us to feature your AI Tool in our newsletter!
Learn AI in 5 Minutes a Day
AI Tool Report is one of the fastest-growing and most respected newsletters in the world, with over 550,000 readers from companies like OpenAI, Nvidia, Meta, Microsoft, and more.
Our research team spends hundreds of hours a week summarizing the latest news, and finding you the best opportunities to save time and earn more using AI.
Sign up with 1-Click
Our LinkedIn Community is growing - Will you join us? We invite you to join our LinkedIn group to participate in AI discussions and share developments with the rest of the group. Join today!
Careers in AI: Top Picks
Explore leading career opportunities in the artificial intelligence industry. 'Careers in AI: Top Picks' brings you the latest job openings from top companies, helping you advance your career in AI. We will update this section as we discover new career opportunities from reputable companies.
- OpenAI Careers… (several other bullets for job postings)
Master AI: Courses & Resources
Explore the world of artificial intelligence with our curated selection of courses and resources designed to elevate your skills and expertise in AI. We will update this section as we discover new courses in AI.
- Google AI Essentials: With Google AI Essentials, you’ll learn how to use generative AI tools to help speed up daily tasks, make more informed decisions, and develop new ideas and content. Receive a sharable certificate to add to your LinkedIn profile.
- Google Cloud Skills Boost: … (continues with several other courses)
Support Our Sponsors:
-Excelsa Coffee: Not Arabica. Not Robusta. Excelsa… (continues with several other sponsor plugs)
Become A Sponsor of Our Newsletter!
Enhance your brand's visibility and drive new opportunities! By becoming a sponsor of our newsletter, you'll gain unparalleled brand exposure and a unique chance to increase traffic and sales through direct engagement with our dedicated and targeted audience.
We can feature an article or AI tool, or simply offer a discount to our subscribers for your product or service. Get in touch with us today - Let's collaborate to create a meaningful impact for your business!
Update your email preferences or unsubscribe here
© 2024 AiNews.com"

Output: "{"sections":[{"section_title":"Headlines","section_content":"Today's Headlines: - Virginia Candidate Hosts Debate Against Incumbent's AI Chatbot - Bentley Hensel, an independent congressional candidate in Virginia, has created an AI chatbot named DonBot to stand in for Democratic incumbent Don Beyer in a recent debate. - Elon Musk's X Allows... (continued with 6 more one-sentence stories)"},{"section_title":"AI Tutorial","section_content":"AI In Action: Quick Tutorials In this section, you'll find short, practical tutorials that walk you through using the latest AI tools, helping you quickly unlock their full potential. Today's AI in Action: Kling AI, one of the most popular AI video generators, now lets you add strategic movement to specific elements in AI video, providing more control in your generated clips. Step-by-step:... (continues with implementation steps and tips)"},{"section_title":"AI Tools","section_content":"AI Tools: - ObjectRemover: Remove any object from your photos quickly and accurately with an AI-driven tool. - EditApp: ... (continues with several other AI tools) Get in touch with us to feature your AI Tool in our newsletter!"},{"section_title":"Job Postings","section_content":"Careers in AI: Top Picks Explore leading career opportunities in the artificial intelligence industry. 'Careers in AI: Top Picks' brings you the latest job openings from top companies, helping you advance your career in AI. We will update this section as we discover new career opportunities from reputable companies. - OpenAI Careers... (several other bullets for job postings)"},{"section_title":"Courses","section_content":"Master AI: Courses & Resources Explore the world of artificial intelligence with our curated selection of courses and resources designed to elevate your skills and expertise in AI. We will update this section as we discover new courses in AI. - Google AI Essentials: With Google AI Essentials, you'll learn how to use generative AI tools to help speed up daily tasks, make more informed decisions, and develop new ideas and content. Receive a sharable certificate to add to your LinkedIn profile. - Google Cloud Skills Boost: ... (continues with several other courses)"}]}"

Explanation: "This is a good example because it correctly notices that there is no main story but rather a series of short secondary stories all under one "headlines" section. It also correctly deciphers the content from the sponsored posts, including the tutorial, job postings, ai tools, and ai courses and including these in full, and recognizing the sponsor/promotional content like the newsletter and linkedin community plugs and the sponsored list at the end. It also included the full content of each section, not truncating or summarizing any of it."
""",
    }

    user_message = {
        "role": "user",
        "content": f"{content}",
    }
    response = await call_language_model(system_message, user_message, "high")
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
