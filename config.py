import os
from dotenv import load_dotenv


def load_env_variables():
    load_dotenv(dotenv_path="beehiiv.env")


def get_config():
    return {
        "twitter_api_key": os.environ["TWITTER_API_KEY"],
        "twitter_api_secret": os.environ["TWITTER_API_SECRET"],
        "twitter_access_key": os.environ["TWITTER_ACCESS_TOKEN"],
        "twitter_access_secret": os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        "openai_api_key": os.environ["OPENAI_API_KEY"],
        "beehiiv_api_key": os.environ["BEEHIIV_API_KEY"],
        "beehiiv_url": os.environ["BEEHIIV_URL"],
        "publication_id": os.environ["PUBLICATION_ID"],
        "subscribe_url": os.environ.get("SUBSCRIBE_URL", ""),
    }
