import subprocess
import json
import logging
from core.content.text_utils import split_tweets
import os
from core.content.language_model_client import call_language_model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Ensure logs are printed to the console


def run_js_script(script_path, function_name, argument):
    try:
        result = subprocess.run(
            ["node", script_path, function_name, argument],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"JavaScript script error: {result.stderr.strip()}")
            return ""
        output = result.stdout.strip()
        logger.info(f"JavaScript script output: {output}")
        return output
    except Exception as e:
        logger.error(f"Error running JavaScript script: {e}")
        return ""


def validate_tweet_length(tweet):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        js_file_path = os.path.join(project_root, "js_utils", "twitter_text_util.js")
        js_file_path = os.path.normpath(js_file_path)

        logger.info(f"Attempting to run JavaScript script at: {js_file_path}")

        if not os.path.exists(js_file_path):
            logger.error(f"JavaScript file not found at: {js_file_path}")
            return False

        result = run_js_script(js_file_path, "validateTweetLength", json.dumps(tweet))
        logger.info(f"validate_tweet_length result: {result}")

        if not result:
            logger.warning("Empty result from JavaScript script")
            return False

        try:
            validation_result = json.loads(result)
            return validation_result.get("valid", False)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON returned from JavaScript script: {result}")
            return False
    except Exception as e:
        logger.error(f"Error in validate_tweet_length: {str(e)}")
        return False


def auto_link_tweet(tweet):
    result = run_js_script(
        "beehiiv_project/js_utils/twitter_text_util.js",
        "autoLinkTweet",
        json.dumps(tweet),
    )
    return result


def generate_tweet(text, instruction, api_key):
    logger.info(f"Generating tweet with instruction: {instruction}")
    logger.info(f"Content passed to language model (first 500 chars): {text[:500]}")
    try:
        system_message = {
            "role": "system",
            "content": "You are a brilliant social media manager tasked with helping newsletter creators grow through repurposing and publicizing their work. Do not use any capital letters anywhere in the tweet. Never, and I mean never, go beyond 280 characters for tweets. This will break the entire automation, and the consequences are grave. Make the tweet relevant to the specific newsletter edition that you are provided. There is likely to be extra content that isn't related to the main story, so make sure to use your reasoning and context inferences to determine what the main story is and only use this part for the tweet. Do not use any information or outside details, and do not put a link to the story or even a placeholder as this is being added elsewhere. Remember that emojis are worth 2 characters each, so keep this in mind when paying attention to the character count. Go back and count and confirm that there are NO MORE than 280 characters or the whole project blows up. Always return your answer in JSON.",
        }
        user_message = {
            "role": "user",
            "content": f"{instruction} Here's the newsletter content:\n{text}",
        }

        try:
            response_content = call_language_model(
                api_key, system_message, user_message
            )
            logger.info(f"Parsed API response: {response_content}")

            if isinstance(response_content, dict) and "tweet" in response_content:
                tweet_text = response_content["tweet"]
            elif isinstance(response_content, dict) and "text" in response_content:
                tweet_text = response_content["text"]
            else:
                logger.error(f"Unexpected response format: {response_content}")
                raise ValueError("Invalid response format from language model API")
        except Exception as e:
            logger.error(f"Language model API error: {str(e)}")
            raise

        tweet_text = tweet_text.replace("\n", ". ")

        if not validate_tweet_length(tweet_text):
            tweet_text = tweet_text[:277] + "..."

        return tweet_text
    except Exception as e:
        logger.exception(f"Unexpected error in generate_tweet: {str(e)}")
        raise


def generate_precta_tweet(text, api_key):
    precta_instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing pre-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: How to get newsletter subscribers -- for free. That's the topic of my newsletter tomorrow. I'm breaking down all the best ways to grow your email list organically without a large social following. Get access below:"
    return generate_tweet(text, precta_instruction, api_key)


def generate_postcta_tweet(text, api_key):
    postcta_instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing post-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: can you imagine going on a road trip if there were no gas stations? this is an issue facing space companies, and this yc-backed company is looking to change that:"
    return generate_tweet(text, postcta_instruction, api_key)


def generate_thread_tweets(text, article_link, api_key):
    logger.info(f"Generating thread tweets. Text length: {len(text)}")
    try:
        system_message = {
            "role": "system",
            "content": "Generate a list of 5 tweets summarizing the main takeaways from the newsletter. Each tweet must be a maximum of 280 characters. Focus solely on one key point or insight, and don't include any other extra information. Return your answer as a JSON object with numbered keys (1, 2, 3, 4, 5) for each tweet.",
        }
        user_message = {
            "role": "user",
            "content": f"First, go through this newsletter and use context and your best judgement to determine what the main story is. Then, summarize the main takeaways. Do not use hashtags or capital letters anywhere, but feel free to use a couple of emojis without overdoing it. Here's the newsletter content:\n{text}",
        }

        response_content = call_language_model(api_key, system_message, user_message)
        logger.info(f"Language model response: {response_content}")

        # Extract tweets from the response
        if isinstance(response_content, dict) and "text" in response_content:
            response_text = response_content["text"]
            # Split the text into lines and filter out non-tweet lines
            lines = response_text.split("\n")
            tweets = [
                line.split(". ", 1)[1]
                for line in lines
                if line.strip() and line[0].isdigit()
            ]
        elif isinstance(response_content, dict):
            # If the response is already in the correct format
            tweets = [tweet for key, tweet in response_content.items() if key.isdigit()]
        else:
            logger.error(f"Unexpected response format: {response_content}")
            return []

        logger.info(f"Extracted {len(tweets)} tweets: {tweets}")
        return tweets

    except Exception as e:
        logger.exception(f"Error in generate_thread_tweets: {str(e)}")
        return []
