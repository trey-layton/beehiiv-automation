from core.content.language_model_client import call_language_model


async def generate_tweets(classification: str, summary: str):
    system_message = {
        "role": "system",
        "content": f"You are a tweet generator for {classification} type content. Create engaging tweets based on the provided summary.",
    }
    user_message = {
        "role": "user",
        "content": f"Generate tweets for the following summary:\n\n{summary}",
    }
    response = await call_language_model(system_message, user_message)
    return response
