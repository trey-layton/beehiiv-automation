import anthropic
from config import get_config
import logging

logger = logging.getLogger(__name__)


def generate_tweet(text):
    try:
        config = get_config()
        client = anthropic.Anthropic(api_key=config["anthropic_api_key"])
        message = client.messages.create(
            model="claude-instant-1.2",
            max_tokens=100,
            temperature=0.0,
            system="""'Turn the following newsletter into a pre-newsletter CTA encouraging people on social media to subscribe to not miss the insights to be found in the newsletter. Make the tweet relevant to the newsletter, example: "How to get newsletter subscribers -- for free. That's the topic of my newsletter tomorrow. I'm breaking down all the best ways to grow your email list organically without a large social following. Get access below:' Do not use uppercase letters, add an entire blank line of text between sentences, and do not use any punctuation marks except for colons and question marks. Make a super strong hook and don't give too much away about the newsletter, instead just convincing the reader to subscribe by telling them what they will learn.""",
            messages=[{"role": "user", "content": text}],
        )

        if isinstance(message.content, list):
            tweet_text = message.content[0].text.strip()
        else:
            tweet_text = message.content.text.strip()

        return tweet_text
    except Exception as e:
        logger.exception("Error while generating tweet:")
        raise
