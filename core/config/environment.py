import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment():
    # Get the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Path to the .env file
    dotenv_path = os.path.join(project_root, ".env")

    # Load the .env file
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logger.info(f"Loaded environment variables from {dotenv_path}")
    else:
        logger.error(f".env file not found at {dotenv_path}")

    # Check if all required environment variables are set
    required_vars = [
        "DISCORD_BOT_TOKEN",
        "DISCORD_APP_ID",
        "GUILD_ID",
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ]

    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"Environment variable {var} is not set.")


def get_config():
    return {
        "discord_bot_token": os.getenv("DISCORD_BOT_TOKEN"),
        "discord_app_id": os.getenv("DISCORD_APP_ID"),
        "guild_id": os.getenv("GUILD_ID"),
        "twitter_api_key": os.getenv("TWITTER_API_KEY"),
        "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    }
