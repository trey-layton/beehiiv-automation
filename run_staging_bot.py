import os
import sys
import logging
from dotenv import load_dotenv
from core.discord_functionality.discord_bot import run_discord_bot
from core.config.environment import get_config
from core.encryption.encryption import ensure_key_exists, get_key_path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Print current working directory
logger.info(f"Current working directory: {os.getcwd()}")

# Explicitly set the environment to staging
os.environ["ENV"] = "staging"

# Load staging environment variables
logger.info("Attempting to load .env.staging file")
load_dotenv(".env.staging")
logger.info("Finished attempt to load .env.staging file")

# Explicitly set and print the STACK_AUTH_API_URL
os.environ["STACK_AUTH_API_URL"] = "https://app.stack-auth.com/api/v1"
logger.info(f"STACK_AUTH_API_URL set to: {os.environ.get('STACK_AUTH_API_URL')}")

# Get configuration for staging
logger.info("Getting staging configuration")
config = get_config(env="staging")
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
