import logging
import sys
from logging.handlers import RotatingFileHandler
import asyncio
import os
from core.config.environment import load_environment, get_config
from core.encryption.encryption import ensure_key_exists, get_key_path
from core.discord_functionality.discord_bot import run_discord_bot
from core.config.user_config import init_db, DB_PATH


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = logging.FileHandler("debug.log", mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Disable propagation for discord.py logs to avoid duplicate logging
    logging.getLogger("discord").propagate = False
    logging.getLogger("discord.http").setLevel(logging.INFO)

    return logger


# Set up logging globally
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    try:
        logger.info("Starting the Discord bot")
        load_environment()
        config = get_config()

        if not config["discord_bot_token"]:
            logger.error("Discord bot token is not set in the environment variables.")
            return

        key_path = get_key_path()
        logger.info(f"Ensuring encryption key exists at: {key_path}")
        ensure_key_exists(key_path)

        logger.info(f"Database path: {DB_PATH}")
        if os.path.exists(DB_PATH):
            logger.info(f"Database file exists. Size: {os.path.getsize(DB_PATH)} bytes")
        else:
            logger.info("Database file does not exist. It will be created.")

        logger.info("Initializing database")
        init_db()

        logger.info("Running Discord bot")
        client = run_discord_bot(config)

        await client.start(config["discord_bot_token"])

    except Exception as e:
        logger.exception("An error occurred while running the Discord bot:")
    finally:
        logger.info("Discord bot shutting down")


if __name__ == "__main__":
    asyncio.run(main())
