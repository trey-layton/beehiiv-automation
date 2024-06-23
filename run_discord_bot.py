import logging
import asyncio
import os
from core.config.environment import load_environment, get_config
from core.encryption.encryption import load_key
from core.discord_functionality.discord_bot import run_discord_bot
from core.config.user_config import init_db, DB_PATH

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

        key_path = "core/config/secret.key"
        logger.info(f"Loading encryption key from {key_path}")
        key = load_key(key_path)

        logger.info(f"Database path: {DB_PATH}")
        if os.path.exists(DB_PATH):
            logger.info(f"Database file exists. Size: {os.path.getsize(DB_PATH)} bytes")
        else:
            logger.info("Database file does not exist. It will be created.")

        logger.info("Initializing database")
        init_db()

        logger.info("Running Discord bot")
        client = run_discord_bot(config, key)
        await client.start(config["discord_bot_token"])

    except Exception as e:
        logger.exception("An error occurred while running the Discord bot:")


if __name__ == "__main__":
    asyncio.run(main())
