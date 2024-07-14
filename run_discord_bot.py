import os
import sys
import logging
from dotenv import load_dotenv
from core.discord_functionality.discord_bot import run_discord_bot
from core.config.environment import get_config
from core.encryption.encryption import ensure_key_exists, get_key_path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Print current working directory
logger.info(f"Current working directory: {os.getcwd()}")

# Load production environment variables
logger.info("Attempting to load .env file")
load_dotenv(".env")
logger.info("Finished attempt to load .env file")

# Get configuration for production
logger.info("Getting production configuration")
config = get_config(env="production")
logger.info(f"Loaded configuration keys: {config.keys()}")

# Ensure the encryption key exists
key_path = get_key_path()
ensure_key_exists(key_path)

# Print the bot token being used (first 10 characters)
logger.info(
    f"Using Discord bot token: {config.get('discord_bot_token', 'Not found')[:10]}..."
)

# Run the bot
bot = run_discord_bot(config)
bot.run(config["discord_bot_token"])
