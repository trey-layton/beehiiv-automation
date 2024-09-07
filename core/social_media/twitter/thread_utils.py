from typing import List, Dict


def restructure_thread(
    tweets: List[Dict[str, str]], web_url: str, subscribe_url: str
) -> List[Dict[str, str]]:
    # Ensure we have at least one tweet
    if not tweets:
        tweets = [{"text": "Check out our latest content!", "type": "content"}]

    # Separate content tweets from special tweets
    content_tweets = [tweet for tweet in tweets if tweet["type"] == "content"]

    # Create or update the article link tweet
    article_tweet = next(
        (tweet for tweet in tweets if tweet["type"] == "article_link"), None
    )
    if article_tweet is None:
        article_tweet = {
            "type": "article_link",
            "text": f"Want to dive deeper? Read the full article here: {web_url}",
        }
    else:
        article_tweet["text"] = (
            f"Want to dive deeper? Read the full article here: {web_url}"
        )

    # Create or update the quote tweet
    quote_tweet = next(
        (tweet for tweet in tweets if tweet["type"] == "quote_tweet"), None
    )
    if quote_tweet is None:
        quote_tweet = {
            "type": "quote_tweet",
            "text": f"If you found this thread valuable, please like and share! Subscribe for more content: {subscribe_url}",
        }

    # Combine all tweets in the correct order
    return content_tweets + [article_tweet, quote_tweet]
