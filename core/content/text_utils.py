import re


def split_tweets(response_content: str, max_length: int = 280) -> list[str]:
    """
    Split the thread text into individual tweets.

    Args:
    response_content (str): The full text to be split into tweets.
    max_length (int): Maximum length of each tweet. Defaults to 280.

    Returns:
    list[str]: List of tweets.
    """
    # Split the thread text into individual tweets using <br> as the delimiter
    thread_tweets = response_content.split("<br>")

    # Remove any leading or trailing whitespace from each tweet
    thread_tweets = [tweet.strip() for tweet in thread_tweets]

    # Further split any tweets that are still too long
    final_tweets = []
    for tweet in thread_tweets:
        if len(tweet) <= max_length:
            final_tweets.append(tweet)
        else:
            words = tweet.split()
            current_tweet = ""
            for word in words:
                if len(current_tweet) + len(word) + 1 <= max_length:
                    current_tweet += " " + word if current_tweet else word
                else:
                    final_tweets.append(current_tweet.strip())
                    current_tweet = word
            if current_tweet:
                final_tweets.append(current_tweet.strip())

    return final_tweets


def clean_text(text: str) -> str:
    """
    Clean the input text by removing extra whitespace and special characters.

    Args:
    text (str): The text to be cleaned.

    Returns:
    str: Cleaned text.
    """
    # Remove extra whitespace
    text = " ".join(text.split())

    # Remove special characters except for common punctuation
    text = re.sub(r"[^\w\s.,!?-]", "", text)

    return text.strip()


def truncate_text(text: str, max_length: int = 280, ellipsis: str = "...") -> str:
    """
    Truncate the text to a maximum length, adding an ellipsis if truncated.

    Args:
    text (str): The text to be truncated.
    max_length (int): Maximum length of the truncated text. Defaults to 280.
    ellipsis (str): The ellipsis to add if the text is truncated. Defaults to '...'.

    Returns:
    str: Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(ellipsis)] + ellipsis
