import os
import sys
import logging
from dotenv import load_dotenv
from core.discord_functionality.discord_bot import run_discord_bot
from core.config.environment import get_config
from core.encryption.encryption import ensure_key_exists, get_key_path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Print current working directory and Python version
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Python version: {sys.version}")

# Print environment
logger.info(f"Current environment: {os.getenv('ENV', 'Not set')}")

# Explicitly set the environment to staging
os.environ["ENV"] = "staging"
logger.info(f"Set environment to: {os.environ['ENV']}")

# Load staging environment variables
logger.info("Attempting to load .env.staging file")
load_dotenv(".env.staging")
logger.info("Finished attempt to load .env.staging file")

# Print all environment variables (be careful with sensitive data)
logger.debug("Environment variables:")
for key, value in os.environ.items():
    if key.startswith(("DISCORD_", "TWITTER_", "OPENAI_", "ANTHROPIC_", "STACK_")):
        logger.debug(f"{key}: {'*' * min(len(value), 10)}")  # Mask the value
    else:
        logger.debug(f"{key}: {value}")

# Get configuration for staging
logger.info("Getting staging configuration")
config = get_config(env="staging")
logger.info(f"Loaded configuration keys: {config.keys()}")

# Print the first few characters of sensitive config values
for key in [
    "discord_bot_token",
    "twitter_api_key",
    "openai_api_key",
    "anthropic_api_key",
]:
    if key in config:
        logger.info(f"{key}: {'*' * min(len(config[key]), 10)}")

# Ensure the encryption key exists
key_path = get_key_path()
ensure_key_exists(key_path)
logger.info(f"Encryption key path: {key_path}")

# Run the bot
bot = run_discord_bot(config)
logger.info("Starting bot...")
bot.run(config["discord_bot_token"])
