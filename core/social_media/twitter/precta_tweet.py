from core.models.account_profile import AccountProfile
from core.content.language_model_client import call_language_model


async def generate_precta_tweet(text: str, account_profile: AccountProfile) -> list:
    instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing pre-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: `How to get newsletter subscribers -- for free. That's the topic of my newsletter tomorrow. I'm breaking down all the best ways to grow your email list organically without a large social following. Get access below:` but combine this content type with the writer's actual social media style (tone, syntax, punctuation, etc)"
    system_message = {
        "role": "system",
        "content": "You are a brilliant social media manager tasked with creating engaging tweets. Create a tweet of up to 280 characters (including spaces and emojis) based on the given content. The tweet should be catchy, informative, and ready to post as-is. Do not include any additional text, formatting, or placeholders. Never, ever add links. These will always be handled elsewhere. More than anything, don't come off as spammy and AI-generated. You will be fired if you do. Examples of things that really hint at AI-written content: too many emojis, too enthusiastic, generic phrases, cliches, etc. For any arguments or reasoning-based content, do not generate your own argument but rather use the logic and ideas discussed in the newsletter. Once again, I cannot emphasize enough how important it is to embody the writer's unique writing style, both in their social posts and in their actual newsletter. Return only the post content, no intro or filler like 'here's a catchy tweet' or anything related. After the post content, identify the type of post (pre-newsletter CTA with a 280-character limit, thread where each individual tweet has a 280 character limit, LinkedIn post with no limit, etc) so that your editor knows his constraints.",
    }

    user_message = {
        "role": "user",
        "content": f"{instruction} Here's the newsletter content:\n{text}",
    }
    main_tweet = await call_language_model(system_message, user_message, tier="high")
    reply_tweet = f"If this sounds interesting, subscribe for free to get it in your inbox! {account_profile.subscribe_url}"

    return [
        {"type": "main_tweet", "text": main_tweet},
        {"type": "reply_tweet", "text": reply_tweet},
    ]
