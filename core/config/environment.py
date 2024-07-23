import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment(env="production"):
    logger.info(f"Loading environment: {env}")

    # Clear existing environment variables
    for key in list(os.environ.keys()):
        if key.startswith(("DISCORD_", "TWITTER_", "OPENAI_", "ANTHROPIC_", "STACK_")):
            del os.environ[key]

    # Get the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logger.info(f"Project root: {project_root}")

    # Path to the .env file
    dotenv_path = os.path.join(
        project_root, f".env{'.staging' if env == 'staging' else ''}"
    )

    logger.info(f"Attempting to load env file: {dotenv_path}")

    # Load the .env file
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=True)
        logger.info(f"Loaded environment variables from {dotenv_path}")

        # Print the first few characters of the loaded token for verification
        token = os.getenv("DISCORD_BOT_TOKEN")
        if token:
            logger.info(f"Loaded Discord bot token: {token[:10]}...")
        else:
            logger.warning("Discord bot token not found in environment variables")
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
        "STACK_AUTH_API_URL",
        "STACK_PROJECT_ID",
        "STACK_SECRET_SERVER_KEY",
    ]

    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"Environment variable {var} is not set.")


def get_config(env="production"):
    logger.info(f"Getting config for environment: {env}")
    load_environment(env)
    config = {
        "discord_bot_token": os.getenv("DISCORD_BOT_TOKEN"),
        "discord_app_id": os.getenv("DISCORD_APP_ID"),
        "guild_id": os.getenv("GUILD_ID"),
        "twitter_api_key": os.getenv("TWITTER_API_KEY"),
        "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "stack_auth_api_url": os.getenv("STACK_AUTH_API_URL"),
        "stack_project_id": os.getenv("STACK_PROJECT_ID"),
        "stack_secret_server_key": os.getenv("STACK_SECRET_SERVER_KEY"),
    }
    logger.info(f"Loaded config keys: {config.keys()}")

    # Log the first few characters of each config value
    for key, value in config.items():
        if value:
            logger.debug(f"{key}: {'*' * min(len(value), 10)}")
        else:
            logger.warning(f"{key} is not set")

    return config
