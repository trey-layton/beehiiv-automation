import logging


logger = logging.getLogger(__name__)
logger.info(f"Loading {__name__} module")

instructions = {
    "content_generation": """
    You are an expert social media content creator specializing in carousel posts for LinkedIn.

    Generate content for a carousel of **6-8 images** that summarize the key points of the provided newsletter section.

    ### Style & Content
    - **Professional Tone**: This is for a business/professional audience on LinkedIn.
    - **Paragraph-Length Text**: Each slide should have at least ~2-3 sentences (like a mini thought-leadership piece).
    - **One Main Point per Slide**: Clearly highlight a single concept, data point, or insight that ties directly back to the source content.
    - **Progressive Flow**: Slide by slide, build expertise or authority. The first slide establishes context/credibility; the last slide drives action or engagement.
    - **No Emojis**. If referencing data, it must come from the provided source text—do not invent stats or details.

    ### Potential Slide Outline
    1. **Slide 1 (Intro)**: Spark interest or share a short powerful statement.  
    2. **Slide 2-7**: Detailed points, data, or insights (one core idea per slide).  
    3. **Slide 8 (Conclusion/CTA)**: Encourage the reader to learn more or apply the info (e.g., “Ready to dive deeper? ...”).

    ### Output Format
    Return the post in **JSON** (and no other text) wrapped between `~!` and `!~`, exactly like this:
    ~!{
        "content_type": "carousel_post",
        "content_container": [
            {
                "heading": "Main heading text",
                "subheading": "Smaller text below"
            },
            ...
        ]
    }!~

    These keys (content_type and content_container) are CRITICAL. If you deivate even slightly, our entire pipeline is ruined.
    Each dictionary in "content_container" represents one image slide:
    - "heading": 1 sentences forming the main paragraph for that slide.
    - "subheading": 2-3 sentences expanding on this main point with evidence or support from the newsletter.

    Focus on substance, clarity, and a business-appropriate voice. Avoid filler or guessing. If data or a sponsor is not mentioned in the source, do not include it.
    """,
    "image_relevance": """   
        For this content type, we actually don't support images yet, so return the content EXACTLY like you received it:     
        ~!{
            "content_type": "carousel_post",
            "content_container": [
                {
                    "heading": "Main heading text",
                    "subheading": "Smaller text below"
                },
                ...
            ]
        }!~
        """,
    "content_personalization": """
       For personalizing LinkedIn carousel content:
       1. Match the creator's professional voice and expertise level
       2. Incorporate industry-specific terminology they commonly use
       3. Maintain their typical level of formality
       4. Reflect their unique perspective on industry topics
       5. Keep consistent with their LinkedIn communication style
       6. Include their preferred ways of expressing business concepts
       7. Mirror their approach to sharing professional insights

       Return the edited post in this EXACT format:

        ~!{
            "content_type": "carousel_post",
            "content_container": [
                {
                    "heading": "Main heading text",
                    "subheading": "Smaller text below"
                },
                ...
            ]
        }!~
   """,
    "hook_writing": """
       For LinkedIn carousel first slides:
       1. Establish professional credibility immediately
       2. Present a compelling business problem or insight
       3. Use industry-relevant framing
       4. Promise valuable professional knowledge
       5. Set up expert positioning
       6. Create interest without being sensational
       7. Appeal to business decision-makers

       Return the edited post in this EXACT format:

        ~!{
            "content_type": "carousel_post",
            "content_container": [
                {
                    "heading": "Main heading text",
                    "subheading": "Smaller text below"
                },
                ...
            ]
        }!~
   """,
    "ai_polish": """
       Polish LinkedIn carousel content by:
       1. Removing AI-like business jargon
       2. Ensuring authentic professional voice
       3. Making transitions business-appropriate
       4. Eliminating generic corporate speak
       5. Maintaining genuine thought leadership tone
       6. Ensuring each slide reads naturally in visual format
       7. Preserving professional credibility

       Return the edited post in this EXACT format:

        ~!{
            "content_type": "carousel_post",
            "content_container": [
                {
                    "heading": "Main heading text",
                    "subheading": "Smaller text below"
                },
                ...
            ]
        }!~
   """,
}
