import asyncio
from celery_app import app
from core.models.account_profile import AccountProfile
from core.content.content_fetcher import fetch_beehiiv_content
from core.social_media.twitter.generate_tweets import (
    generate_precta_tweet,
    generate_postcta_tweet,
    generate_thread_tweet,
    generate_long_form_tweet,
)
from core.social_media.linkedin.generate_linkedin_post import generate_linkedin_post


@app.task
def generate_content(account_profile: dict, post_id: str, content_type: str):
    account_profile = AccountProfile(**account_profile)

    # Create an event loop
    loop = asyncio.get_event_loop()

    # Fetch content from Beehiiv
    content_data = loop.run_until_complete(
        fetch_beehiiv_content(account_profile, post_id)
    )

    # Generate content based on type
    if content_type == "precta_tweet":
        return loop.run_until_complete(
            generate_precta_tweet(content_data["free_content"], account_profile)
        )
    elif content_type == "postcta_tweet":
        return loop.run_until_complete(
            generate_postcta_tweet(
                content_data["free_content"], account_profile, content_data["web_url"]
            )
        )
    elif content_type == "thread_tweet":
        return loop.run_until_complete(
            generate_thread_tweet(
                content_data["free_content"], content_data["web_url"], account_profile
            )
        )
    elif content_type == "long_form_tweet":
        return loop.run_until_complete(
            generate_long_form_tweet(content_data["free_content"], account_profile)
        )
    elif content_type == "linkedin":
        return loop.run_until_complete(
            generate_linkedin_post(content_data["free_content"], account_profile)
        )
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


@app.task
def test_redis():
    return "Redis test successful"
