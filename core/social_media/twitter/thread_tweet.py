import json
import re
from core.models.account_profile import AccountProfile
from core.content.language_model_client import call_language_model


async def generate_thread_tweet(
    text: str, account_profile: AccountProfile, web_url: str
) -> list:
    example_tweet = """tweet 1: "A professional sports gambler used analytics to turn a $700,000 loan into more than $300 million.

This is the wild story 👇👇👇"

2: "1) Let's start with some history...

Matthew Benham graduated from the world-renowned University of Oxford in 1989 with a degree in Physics.

He spent the next 12 years working in finance, eventually being named a VP at Bank of America.

But in 2001, he decided to change careers."

3. "2) After leaving Bank of America in 2001, Matthew Benham joined sports gambling company Premier Bet.

His job was to help develop predictive gambling models based on analytics. 

The best part?

Benham learned under one of the most successful gamblers in the world — Tony Bloom."

4. "3) After only a couple years, Matthew Benham and Tony Bloom had a falling out.

The exact reason why isn't clear, but by the time Benham left Premier Bet in 2003, the fire was already lit.

He wasn't going back to investment banking.

He was a professional sports gambler now."

5. "4) Matthew Benham went on to win millions of dollars gambling on sports, but in 2004, he set up his own betting syndicate — Smartodds.

The idea was simple:

Benham consulted clients using the same algorithms, statistics & data research that made him a successful sports gambler."
"""

    system_message = {
        "role": "system",
        "content": "You are a brilliant social media copywriter tasked with managing the social media accounts of the most brilliant, talented creators in the world. Generate a list of 5 tweets summarizing the main takeaways from the newsletter. Each tweet must be a maximum of 280 characters. Focus solely on one key point or insight, and don't include any other extra information. Return your answer as a JSON object with numbered keys (1., 2., 3., 4., 5.) for each tweet. Make sure each has a strong, punchy hook that keeps the reader engaged and motivated to move to the next tweet in the order. Make sure it sounds natural and make sure it flows well as a complete piece. only focus on the most important, big-picture lessons or takeaways from the newsletter. Return ONLY the document, no intro or conclusion text. More than anything, don't come off as spammy and AI-generated. You will be fired if you do. Examples of things that really hint at AI-written content: too many emojis, too enthusiastic, generic phrases, cliches, etc. For any arguments or reasoning-based content, do not generate your own argument but rather use the logic and ideas discussed in the newsletter. Once again, I cannot emphasize enough how important it is to embody the writer's unique writing style, both in their social posts and in their actual newsletter.",
    }

    user_message = {
        "role": "user",
        "content": f"Emulate the writer's actual social media style (tone, syntax, punctuation, etc) as seen in these examples classified by type of newsletter: '{example_tweet}'. Here's the newsletter content:{text}",
    }

    try:
        response_content = await call_language_model(system_message, user_message)
        print(f"\nRaw LLM response: {json.dumps(response_content, indent=2)}")

        tweets = []
        if isinstance(response_content, str):
            print("Response is a string, attempting to parse as JSON")
            try:
                json_str = re.search(r"\{.*\}", response_content, re.DOTALL)
                if json_str:
                    parsed_content = json.loads(json_str.group())
                    if isinstance(parsed_content, dict):
                        for key, tweet in parsed_content.items():
                            if key.rstrip(".").isdigit():
                                tweets.append(
                                    {"text": tweet.strip(), "type": "content"}
                                )
                                print(f"Added tweet: {tweet.strip()}")
                else:
                    print("No valid JSON found in the response")
            except json.JSONDecodeError:
                print("Failed to parse response as JSON")
                lines = response_content.split("\n")
                for line in lines:
                    if line.strip() and not line.strip().startswith(("{", "}")):
                        tweets.append({"text": line.strip(), "type": "content"})
                        print(f"Added tweet from line: {line.strip()}")
        elif isinstance(response_content, dict):
            print("Response is a dictionary")
            for key, tweet in response_content.items():
                if key.rstrip(".").isdigit():
                    tweets.append({"text": tweet.strip(), "type": "content"})
                    print(f"Added tweet: {tweet.strip()}")
        else:
            print(f"Unexpected response type: {type(response_content)}")

        # Add article link tweet
        tweets.append(
            {
                "text": f"If you want to go even deeper, check out the full article! {web_url}",
                "type": "article_link",
            }
        )

        # Add quote tweet
        tweets.append(
            {
                "text": "If you found value in this thread, please give it a like and share!",
                "type": "quote_tweet",
            }
        )

        print(f"\nGenerated {len(tweets)} tweets for the thread")
        print(f"Final tweets: {json.dumps(tweets, indent=2)}")
        return tweets
    except Exception as e:
        print(f"\nError in generate_thread_tweet: {str(e)}")
        raise
