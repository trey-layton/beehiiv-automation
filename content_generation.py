import logging
import json
from openai import OpenAI
from config import get_config

logger = logging.getLogger(__name__)


def generate_article_tweets(text, link):
    try:
        config = get_config()
        client = OpenAI(api_key=config["openai_api_key"])

        system_message = {
            "role": "system",
            "content": "Generate a JSON object with the tweet text under the key 'tweet'. Never, and I mean never, go beyond 280 characters for tweets. This will break the entire automation, and the consequences are grave. Make the tweet relevant to the specific newsletter edition that you are provided, example: 'This startup is the next Youtube. Eggnog is an AI video character creation tool enabling users to create and share their own consistent characters. Click below to learn more about them and see why they're poised to skyrocket:' for a newsletter edition about an AI character and video creation platform called Eggnog in a broader newsletter that talks about YC startups. Don't include the link as that will be posted in a follow-up tweet.",
        }
        user_message = {
            "role": "user",
            "content": f"Turn the following newsletter into a super catchy, intriguing pre-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to subscribe to not miss the insights to be found in the newsletter. I don't want to promote the newsletter as a whole, but rather the specific main story being covered in the newsletter. Do not use uppercase letters anywhere in the tweet. Make a super strong hook and don't give too much away about the newsletter, hinting at what is being talked about in the newsletter but convincing the reader to subscribe by telling them what they will learn. Then, turn it into a post-publish plug that also generates intrigue but will have the actual post to share. Here's an example: 'hamming is building the llm to police all other llms. why is this important, what do i like most, and what are some of the biggest risks they face? check it out in this week's newsletter, now live!'\n\nNewsletter:\n{text}\n\nTweet (output the response in JSON format with the tweet text as the value of the key 'tweet'):",
        }

        logger.info(f"User message content: {user_message['content']}")

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[system_message, user_message],
            max_tokens=100,
            n=1,
            temperature=0.7,
        )

        response_content = response.choices[0].message.content.strip()
        logger.info(f"API response content: {response_content}")

        try:
            tweets_data = json.loads(response_content)
            precta_tweet = tweets_data["tweets"][0]
            postcta_tweet = tweets_data["tweets"][1]
        except (json.JSONDecodeError, KeyError):
            logger.error(
                "The response did not contain the expected JSON structure. Using the raw content."
            )
            precta_tweet = response_content
            postcta_tweet = ""

        precta_tweet = precta_tweet.replace("\n", ". ")
        postcta_tweet = postcta_tweet.replace("\n", ". ")

        if len(precta_tweet) > 280:
            precta_tweet = precta_tweet[:277] + "..."
        if len(postcta_tweet) > 280:
            postcta_tweet = postcta_tweet[:277] + "..."

        return precta_tweet, postcta_tweet
    except Exception as e:
        logger.exception("Error while generating tweets:")
        raise
