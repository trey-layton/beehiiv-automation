import subprocess
import json
import logging
from content.openai_client import call_openai
from content.text_utils import split_tweets
import os
from openai import OpenAIError

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
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root
        project_root = os.path.dirname(current_dir)
        # Construct the path to the JS file
        js_file_path = os.path.join(project_root, "js_utils", "twitter_text_util.js")
        # Normalize the path to resolve any .. or . components
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
            response_content = call_openai(api_key, system_message, user_message)
            logger.info(f"Raw API response: {response_content}")

            if isinstance(response_content, dict) and "tweet" in response_content:
                tweet_text = response_content["tweet"]
            else:
                logger.error(f"Unexpected response format: {response_content}")
                raise ValueError("Invalid response format from OpenAI API")
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API call: {str(e)}")
            raise

        tweet_text = tweet_text.replace("\n", ". ")

        if not validate_tweet_length(tweet_text):
            tweet_text = tweet_text[:277] + "..."

        return tweet_text
    except Exception as e:
        logger.exception(f"Unexpected error in generate_tweet: {str(e)}")
        raise


# Existing functions for generating specific types of tweets
def generate_precta_tweet(text, api_key):
    precta_instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing pre-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: How to get newsletter subscribers -- for free. That's the topic of my newsletter tomorrow. I'm breaking down all the best ways to grow your email list organically without a large social following. Get access below:"
    return generate_tweet(text, precta_instruction, api_key)


def generate_postcta_tweet(text, api_key):
    postcta_instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing post-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: can you imagine going on a road trip if there were no gas stations? this is an issue facing space companies, and this yc-backed company is looking to change that:"
    return generate_tweet(text, postcta_instruction, api_key)


def generate_thread_tweets(text, article_link, api_key):
    try:
        system_message = {
            "role": "system",
            "content": "Generate a list of 5 tweets summarizing the main takeaways from the newsletter. Each tweet must be a maximum of 280 characters. Mark the break between tweets with a <br> where there is no space between the break and the first letter of the next tweet. Focus solely on one key point or insight, and don't include any other extra information. Always return your answer in JSON.",
        }
        user_message = {
            "role": "user",
            "content": f"First, go through this newsletter and use context and your best judgement to determine what the main story is. Then, summarize the main takeaways. Do not use hashtags or capital letters anywhere, but feel free to use a couple of emojis without overdoing it. This example numbers each tweet, but that's just so you can see how long and what types of phrases to use before and after tweet cut offs. You should NOT number your tweets. Here's an example: `#1. Newsletter growth hack I've used to drive 100K+ subscribers: Referral giveaways. Here's how you can use them to do the same for your newsletter (it's much easier than most think): #2. Referral giveaways are fairly simple: Here’s how they work: 1) Give away a product or service for free 2) Subscribers enter to win by sharing their referral link 3) 1 successful referral = 1 entry to win the giveaway These work great for 3 reasons: #3. 1) The Incentives The more subscribers share, the better their shot at winning. Yet subscribers still get a chance to win with 1 referral. This incentive structure is key. You want subscribers to share as much as possible. #4. 2) You don't need a referral program If you don’t have a milestone referral program, that’s ok. You can still do referral giveaways. Use beehiiv’s or SparkLoop’s referral tool to give readers a referral link to share and track results. #5. The subscribers you get will be high-quality. This is because the people being referred don't sign up because of the giveaway. They learn about your newsletter from a friend or co-worker sharing it with them.`:\n{text}",
        }

        response_content = call_openai(api_key, system_message, user_message)

        logger.info(f"Raw API response: {response_content}")

        try:
            thread_data = json.loads(response_content)
            thread_tweets = [tweet for key, tweet in thread_data.items()]
        except (json.JSONDecodeError, KeyError):
            logger.error(
                "The response did not contain the expected JSON structure. Using the raw content."
            )
            thread_tweets = split_tweets(response_content)

        # Ensure the last tweet is the plug tweet
        thread_tweets.append(
            f"for more insights, check out the full article here: {article_link}"
        )

        return thread_tweets
    except Exception as e:
        logger.exception("Error while generating thread tweets:")
        raise
