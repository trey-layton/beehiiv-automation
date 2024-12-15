import logging


logger = logging.getLogger(__name__)


def get_instructions_for_content_type(content_type: str) -> dict:
    # This is a basic implementation. In the future, we can expand this to load
    # more specific instructions for each content type.
    logger.info("get_instructions_for_content_type called in content_type_loader.py")
    return {
        "content_generation": "",
        "structure_analysis": "",
        "content_strategy": "",
        "style_personalization": "",
        "hook": "",
        "ai_detection": "",
        "final_review": "",
        "formatting": {
            "include_reply": False,
            "reply_template": "",
            "is_thread": False,
            "thread_specific": {
                "num_tweets": 0,
                "include_article_link": False,
                "article_link_template": "",
                "include_quote_tweet": False,
                "quote_tweet_text": "",
            },
        },
    }
