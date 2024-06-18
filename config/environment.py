import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment() -> None:
    """
    Loads environment variables from the appropriate .env file based on the environment setting.

    This function checks the 'ENV' environment variable to determine the environment setting
    (default is 'local'). It then loads the environment variables from the corresponding .env file.

    If the environment is 'production', it loads from '/root/beehiiv-automation/.env'.
    Otherwise, it loads from '.env' in the current directory.

    Logs an error if the .env file is not found.
    """
    environment = os.getenv("ENV", "local")
    dotenv_path = (
        "/root/beehiiv-automation/.env" if environment == "production" else ".env"
    )
    if not os.path.exists(dotenv_path):
        logger.error(f".env file not found at {dotenv_path}")
        return
    load_dotenv(dotenv_path=dotenv_path)


def get_config() -> Dict[str, Optional[str]]:
    """
    Retrieves the configuration dictionary from environment variables.

    Loads the environment variables using the load_environment function and constructs
    a dictionary containing the necessary configuration keys and tokens.

    Logs an error for each environment variable that is not set.

    Returns:
        Dict[str, Optional[str]]: Configuration dictionary containing necessary keys and tokens.
    """
    load_environment()
    config = {
        "discord_bot_token": os.getenv("DISCORD_BOT_TOKEN"),
        "discord_app_id": os.getenv("DISCORD_APP_ID"),
        "guild_id": os.getenv("GUILD_ID"),
        "twitter_api_key": os.getenv("TWITTER_API_KEY"),
        "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    }
    for key, value in config.items():
        if value is None:
            logger.error(f"Environment variable {key.upper()} is not set.")
        else:
            logger.info(f"{key.upper()} is set to: {value}")
    return config
