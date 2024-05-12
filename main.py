import logging
from beehiiv import get_beehiiv_post_id, get_beehiiv_post_content
from content_extraction import extract_text
from content_generation import generate_tweet
from config import load_env_variables, get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(beehiiv_url):
    try:
        # Load environment variables from .env file
        load_env_variables()
        # Get the configuration settings
        config = get_config()

        # Extract the post ID from the Beehiiv newsletter URL
        post_id = get_beehiiv_post_id(beehiiv_url)

        # Fetch the HTML content of the Beehiiv post using the API
        html_str = get_beehiiv_post_content(
            config["beehiiv_api_key"], config["publication_id"], post_id
        )
        # Extract the text content from the HTML
        cleaned_text = extract_text(html_str)
        logger.info("Cleaned text:")
        logger.info(cleaned_text)

        # Generate a tweet based on the extracted text using Claude
        tweet = generate_tweet(cleaned_text)
        logger.info("\nTweet:")
        logger.info(tweet)

        return tweet

    except Exception as e:
        logger.exception("An error occurred:")
        return None


if __name__ == "__main__":
    # Get the Beehiiv newsletter URL from user input
    beehiiv_url = input("Enter the Beehiiv newsletter URL: ")
    main(beehiiv_url)
