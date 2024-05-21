import logging
import json
from openai import OpenAI
from config import get_config

logger = logging.getLogger(__name__)


def generate_tweet(text, instruction):
    try:
        config = get_config()
        client = OpenAI(api_key=config["openai_api_key"])

        system_message = {
            "role": "system",
            "content": "Generate a JSON object with the tweet text under the key 'tweet'. Never, and I mean never, go beyond 280 characters for tweets. This will break the entire automation, and the consequences are grave. Make the tweet relevant to the specific newsletter edition that you are provided. There is likely to be extra content that isn't related to the main story, so make sure to use your reasoning and context inferences to determine what the main story is and only use this part for the tweet.",
        }
        user_message = {
            "role": "user",
            "content": f"{instruction} Here’s the newsletter content:\n{text}",
        }

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_message, user_message],
            max_tokens=100,
            n=1,
            temperature=0.3,
        )

        response_content = response.choices[0].message.content.strip()

        logger.info(f"Raw API response: {response_content}")

        try:
            tweet_data = json.loads(response_content)
            tweet_text = tweet_data["tweet"]
        except (json.JSONDecodeError, KeyError):
            logger.error(
                "The response did not contain the expected JSON structure. Using the raw content."
            )
            tweet_text = response_content

        tweet_text = tweet_text.replace("\n", ". ")

        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        return tweet_text
    except Exception as e:
        logger.exception("Error while generating tweet:")
        raise


def generate_precta_tweet(text):
    precta_instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing post-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: How to get newsletter subscribers -- for free. That's the topic of my newsletter tomorrow. I'm breaking down all the best ways to grow your email list organically without a large social following. Get access below:"
    return generate_tweet(text, precta_instruction)


def generate_postcta_tweet(text):
    postcta_instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing post-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: can you imagine going on a road trip if there were no gas stations? this is an issue facing space companies, and this yc-backed company is looking to change that:"
    return generate_tweet(text, postcta_instruction)


def generate_thread_tweets(text, subscribe_url):
    try:
        config = get_config()
        client = OpenAI(api_key=config["openai_api_key"])

        system_message = {
            "role": "system",
            "content": "Generate a list of 5 tweets summarizing the main takeaways from the newsletter. Each tweet must be a maximum of 280 characters. Focus solely on one key point or insight, and don't include any other extra information.",
        }
        user_message = {
            "role": "user",
            "content": f"First, go through this newsletter and use context and your best judgement to determine what the main story is. Then, summarize the main takeaways. Do not use hashtags or capital letters anywhere, but feel free to use a couple of emojis without overdoing it. Here's an example: `#1. Newsletter growth hack I've used to drive 100K+ subscribers: Referral giveaways. Here's how you can use them to do the same for your newsletter (it's much easier than most think): #2. Referral giveaways are fairly simple: Here’s how they work: 1) Give away a product or service for free 2) Subscribers enter to win by sharing their referral link 3) 1 successful referral = 1 entry to win the giveaway These work great for 3 reasons: #3. 1) The Incentives The more subscribers share, the better their shot at winning. Yet subscribers still get a chance to win with 1 referral. This incentive structure is key. You want subscribers to share as much as possible. #4. 2) You don't need a referral program If you don’t have a milestone referral program, that’s ok. You can still do referral giveaways. Use beehiiv’s or SparkLoop’s referral tool to give readers a referral link to share and track results. #5. 3) The subscribers you get will be high-quality. This is because the people being referred don't sign up because of the giveaway. They learn about your newsletter from a friend or co-worker sharing it with them.`:\n{text}",
        }

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_message, user_message],
            max_tokens=1000,
            n=1,
            temperature=0.3,
        )

        response_content = response.choices[0].message.content.strip()

        logger.info(f"Raw API response: {response_content}")

        try:
            thread_data = json.loads(response_content)
            thread_tweets = thread_data["tweets"]
        except (json.JSONDecodeError, KeyError):
            logger.error(
                "The response did not contain the expected JSON structure. Using the raw content."
            )
            thread_tweets = response_content.split("\n")

        # Ensure the last two tweets are the plug and quote tweet
        if len(thread_tweets) < 2:
            raise ValueError(
                "The generated thread is too short. Ensure the newsletter content is sufficient."
            )

        thread_tweets[-2] = (
            f"for more insights, check out my newsletter breaking it down: {subscribe_url}"
        )
        thread_tweets[-1] = (
            f"if you enjoyed this thread, would really appreciate it if you liked or shared! {thread_tweets[0]}"
        )

        return thread_tweets
    except Exception as e:
        logger.exception("Error while generating thread tweets:")
        raise
