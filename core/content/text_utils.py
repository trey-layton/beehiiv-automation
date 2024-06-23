def split_tweets(response_content):
    """
    Split the thread text into individual tweets using <br> as the delimiter.
    """
    # Split the thread text into individual tweets using <br> as the delimiter
    thread_tweets = response_content.split("<br>")

    # Remove any leading or trailing whitespace from each tweet
    thread_tweets = [tweet.strip() for tweet in thread_tweets]

    return thread_tweets
