import subprocess
import json
import logging
from core.content.text_utils import split_tweets, clean_text, truncate_text
import os
from core.content.language_model_client import call_language_model
from core.config.user_config import load_user_config
import re

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Ensure logs are printed to the console


def count_tweet_characters(tweet: str) -> int:
    # URLs are always counted as 23 characters
    url_pattern = r"https?://[\w./]+"
    tweet_without_urls = re.sub(url_pattern, "x" * 23, tweet)

    # Count remaining characters
    return len(tweet_without_urls)


def validate_tweet_length(tweet: str) -> bool:
    return count_tweet_characters(tweet) <= 280


def validate_tweet_length(tweet):
    return {"valid": count_tweet_characters(tweet) <= 280}


import re


def auto_link_tweet(tweet):
    # This is a simplified version and may not catch all cases
    tweet = re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', tweet)
    tweet = re.sub(r"@(\w+)", r'<a href="https://twitter.com/\1">@\1</a>', tweet)
    tweet = re.sub(
        r"#(\w+)", r'<a href="https://twitter.com/hashtag/\1">#\1</a>', tweet
    )
    return tweet


def extract_entities(tweet):
    mentions = re.findall(r"@(\w+)", tweet)
    hashtags = re.findall(r"#(\w+)", tweet)
    urls = re.findall(r"(https?://\S+)", tweet)
    return {"mentions": mentions, "hashtags": hashtags, "urls": urls}


async def generate_tweet(text, instruction, api_key, example_tweet):
    logger.info(f"Generating tweet with instruction: {instruction}")
    logger.info(f"Content passed to language model (first 500 chars): {text[:500]}")
    try:
        system_message = {
            "role": "system",
            "content": "You are a brilliant social media manager tasked with creating engaging tweets. Create a tweet of up to 280 characters (including spaces and emojis) based on the given content. The tweet should be catchy, informative, and ready to post as-is. Do not include any additional text, formatting, or placeholders. Never, ever add links. These will always be handled elsewhere.",
        }
        user_message = {
            "role": "user",
            "content": f"{instruction} Here's the newsletter content:\n{text}\n\nEmulate this tweet style: {example_tweet}",
        }

        response_content = await call_language_model(
            api_key, system_message, user_message
        )
        logger.info(f"Raw API response: {response_content}")

        # Extract tweet text from the response
        if isinstance(response_content, dict):
            tweet_text = (
                response_content.get("tweet") or response_content.get("text") or ""
            )
        elif isinstance(response_content, str):
            tweet_text = response_content
        else:
            logger.error(f"Unexpected response format: {response_content}")
            raise ValueError("Invalid response format from language model API")

        # Clean up the tweet text
        tweet_text = clean_tweet_text(tweet_text)

        # Ensure the tweet is not longer than 280 characters
        if len(tweet_text) > 280:
            logger.warning(f"Tweet too long ({len(tweet_text)} chars). Truncating.")
            tweet_text = tweet_text[:277] + "..."

        logger.info(f"Final tweet text (length {len(tweet_text)}): {tweet_text}")
        # If the tweet is still too long, try to shorten it
        if len(tweet_text) > 265:
            logger.info("Tweet is too long. Requesting a shorter version.")
            tweet_text = await shorten_tweet(tweet_text, api_key)

        logger.info(f"Final tweet text (length {len(tweet_text)}): {tweet_text}")
        return tweet_text
    except Exception as e:
        logger.exception(f"Unexpected error in generate_tweet: {str(e)}")
        raise


def clean_tweet_text(tweet_text):
    # Remove any surrounding quotes and whitespace
    tweet_text = tweet_text.strip().strip('"')

    # Replace multiple spaces with a single space
    tweet_text = re.sub(r"\s+", " ", tweet_text)

    # Remove any "Tweet:" or similar prefixes
    tweet_text = re.sub(r"^(Tweet:?\s*)", "", tweet_text, flags=re.IGNORECASE)

    return tweet_text


async def shorten_tweet(tweet_text, api_key):
    shorten_system_message = {
        "role": "system",
        "content": "You are tasked with shortening the given tweet to exactly 265 characters or less while maintaining its core message and engagement potential. The shortened tweet should be ready to post as-is, without any additional text or formatting. Never add links, and never add a CTA to subscribe as this will be handled elsewhere.",
    }
    shorten_user_message = {
        "role": "user",
        "content": f"Shorten this tweet to 265 characters or less:\n{tweet_text}",
    }

    shortened_response = await call_language_model(
        api_key, shorten_system_message, shorten_user_message
    )

    if isinstance(shortened_response, dict):
        shortened_tweet = (
            shortened_response.get("tweet") or shortened_response.get("text") or ""
        )
    elif isinstance(shortened_response, str):
        shortened_tweet = shortened_response
    else:
        logger.error(
            f"Unexpected response format for shortened tweet: {shortened_response}"
        )
        raise ValueError(
            "Invalid response format from language model API for shortened tweet"
        )

    return clean_tweet_text(shortened_tweet)[:265]


async def generate_precta_tweet(text, api_key, example_tweet):
    precta_instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing pre-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: `How to get newsletter subscribers -- for free. That's the topic of my newsletter tomorrow. I'm breaking down all the best ways to grow your email list organically without a large social following. Get access below:` but combine this content type with the writer's actual social media style (tone, syntax, punctuation, etc): '{example_tweet}'"
    return await generate_tweet(text, precta_instruction, api_key, example_tweet)


async def generate_postcta_tweet(text, api_key, example_tweet):
    postcta_instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing post-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: `can you imagine going on a road trip if there were no gas stations? this is an issue facing space companies, and this yc-backed company is looking to change that:` but combine this content type with the writer's actual social media style (tone, syntax, punctuation, etc): '{example_tweet}'"
    return await generate_tweet(text, postcta_instruction, api_key, example_tweet)


async def generate_thread_tweets(text, article_link, api_key, example_tweet):
    logger.info(f"Generating thread tweets. Text length: {len(text)}")
    try:
        system_message = {
            "role": "system",
            "content": "You are a brilliant social media copywriter tasked with managing the social media accounts of the most brilliant, talented creators in the world. Generate a list of 5 tweets summarizing the main takeaways from the newsletter. Each tweet must be a maximum of 280 characters. Focus solely on one key point or insight, and don't include any other extra information. Return your answer as a JSON object with numbered keys (1., 2., 3., 4., 5.) for each tweet. Make sure each has a strong, punchy hook that keeps the reader engaged and motivated to move to the next tweet in the order. Make sure it sounds natural and make sure it flows well as a complete piece. only focus on the most important, big-picture lessons or takeaways from the newsletter. Return ONLY the document, no intro or conclusion text.",
        }
        user_message = {
            "role": "user",
            "content": f"First, go through this newsletter and use context and your best judgement to determine what the main story is. Then, summarize the main takeaways. Emulate the writer's actual social media style (tone, syntax, punctuation, etc) as seen in this example:'{example_tweet}' Here's the newsletter content:\n{text}",
        }

        response_content = await call_language_model(
            api_key, system_message, user_message
        )
        logger.info(f"Language model response: {response_content}")

        tweets = []
        if isinstance(response_content, dict) and "text" in response_content:
            response_text = response_content["text"]
            tweet_pattern = r"\d+\.\s*(.+?)(?=\n\d+\.|\Z)"
            tweets = [
                match.group(1).strip()
                for match in re.finditer(tweet_pattern, response_text, re.DOTALL)
            ]
        elif isinstance(response_content, dict):
            tweets = [
                tweet.strip()
                for key, tweet in response_content.items()
                if key.isdigit()
            ]

        cleaned_tweets = [clean_text(tweet.strip()) for tweet in tweets]
        truncated_tweets = [
            truncate_text(tweet, max_length=280) for tweet in cleaned_tweets
        ]
        article_tweet = {
            "text": f"if you want to go even deeper, check out the full article! {article_link}",
            "type": "article_link",
        }
        truncated_tweets.append(article_tweet)
        quote_tweet = {
            "text": "and if you found value in this thread, please give it a like and share!",
            "type": "quote_tweet",
        }
        truncated_tweets.append(quote_tweet)
        logger.info(
            f"Extracted and processed {len(truncated_tweets)} tweets: {truncated_tweets}"
        )
        return truncated_tweets

    except Exception as e:
        logger.exception(f"Error in generate_thread_tweets: {str(e)}")
        return []


async def generate_long_form_tweet(text, api_key, example_tweet):
    logger.info("Generating long-form tweet")
    logger.info(f"Content passed to language model (first 500 chars): {text[:500]}")
    try:
        system_message = {
            "role": "system",
            "content": "You are a skilled social media ghost writer creating engaging long-form tweets for a top creator. Generate a tweet of approximately 850 characters that summarizes the main points of the given content. Each sentence should be on a new line, separated by <br>. The tweet should be informative, engaging, and ready to post manually. Do not include any additional text, formatting, or placeholders beyond the <br> separators. ONLY return the Tweet text, skipping any intro or conclusion text. Use a strong hook, but don't make it too clickbaity, and focus on the big picture. Make the post flow... you're telling the story, not making it choppy.",
        }
        user_message = {
            "role": "user",
            "content": f"Create a long-form tweet summarizing this newsletter content. Use a style similar to this example: {example_tweet}\n\nHere's the newsletter content:\n{text}",
        }

        response_content = await call_language_model(
            api_key, system_message, user_message
        )
        logger.info(f"Raw API response: {response_content}")

        # Extract tweet text from the response
        if isinstance(response_content, dict):
            tweet_text = (
                response_content.get("tweet") or response_content.get("text") or ""
            )
        elif isinstance(response_content, str):
            tweet_text = response_content
        else:
            logger.error(f"Unexpected response format: {response_content}")
            raise ValueError("Invalid response format from language model API")

        # Clean up the tweet text
        tweet_text = tweet_text.strip().strip('"')
        tweet_text = tweet_text.replace("\n", "<br>")
        tweet_text = tweet_text.replace("<br><br>", "<br>")
        tweet_text = re.sub(r"^(Tweet:?\s*)", "", tweet_text, flags=re.IGNORECASE)

        logger.info(
            f"Final long-form tweet text (length {len(tweet_text)}):\n{tweet_text}"
        )
        return tweet_text
    except Exception as e:
        logger.exception(f"Unexpected error in generate_long_form_tweet: {str(e)}")
        raise
