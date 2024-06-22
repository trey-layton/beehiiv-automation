import sys
import os

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, Dict, Any

# Import necessary handlers
from discord_functionality.discord_utils import load_user_config
from discord_functionality.discord_events_handler import (
    on_ready as on_ready_event,
    on_message,
)
from discord_functionality.discord_commands_handler import (
    set_config_command,
    run_script_command,
)

# Configure logging
logging.basicConfig(level=logging.INFO)


def run_discord_bot(config: Dict[str, Any], key: bytes) -> None:
    """
    Initializes and runs the Discord bot.

    Args:
        config (Dict[str, Any]): Configuration dictionary.
        key (bytes): Encryption key.
    """
    DISCORD_BOT_TOKEN = config.get("discord_bot_token")

    if not DISCORD_BOT_TOKEN:
        raise ValueError("Discord bot token not found in configuration.")

    # Log the bot token to confirm retrieval
    logging.info(f"Using Discord bot token: {DISCORD_BOT_TOKEN}")

    # Create a bot instance
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    # Register event handlers
    @bot.event
    async def on_ready() -> None:
        """
        Event handler for when the bot is ready.
        Calls the on_ready function from discord_events_handler.
        """
        try:
            await on_ready_event(bot, config)
            logging.info("Bot is ready and commands are synced.")
        except Exception as e:
            logging.exception("Error during on_ready event:")
            raise

    @bot.event
    async def on_message(message: discord.Message) -> None:
        """
        Event handler for when a message is received.
        Calls the on_message function from discord_events_handler.

        Args:
            message (discord.Message): The received message.
        """
        try:
            user_config = load_user_config(key)
            await on_message(bot, message, user_config, key, config)
        except Exception as e:
            logging.exception("Error during on_message event:")
            raise

    # Register command handlers
    @bot.tree.command(name="set_config", description="Set user configuration")
    @app_commands.describe(
        beehiiv_api_key="Your Beehiiv API key",
        subscribe_url="Your subscribe URL",
        publication_id="Your publication ID",
    )
    async def set_config(
        interaction: discord.Interaction,
        beehiiv_api_key: str,
        subscribe_url: str,
        publication_id: str,
    ) -> None:
        """
        Command to set user configuration.

        Args:
            interaction (discord.Interaction): The interaction instance.
            beehiiv_api_key (str): The user's Beehiiv API key.
            subscribe_url (str): The subscription URL.
            publication_id (str): The publication ID.
        """
        try:
            user_config = load_user_config(key)
            await set_config_command(
                interaction,
                beehiiv_api_key,
                subscribe_url,
                publication_id,
                user_config,
                key,
                config,
            )
        except Exception as e:
            logging.exception("Error during set_config command:")
            await interaction.response.send_message(
                "Failed to set configuration. Please try again later.", ephemeral=True
            )

    @bot.tree.command(name="run_script", description="Run the main script")
    @app_commands.describe(
        edition_url="Edition URL",
        precta="Include pre CTA",
        postcta="Include post CTA",
        thread="Create a thread",
    )
    async def run_script(
        interaction: discord.Interaction,
        edition_url: str,
        precta: bool = False,
        postcta: bool = False,
        thread: bool = False,
    ) -> None:
        """
        Command to run the main script.

        Args:
            interaction (discord.Interaction): The interaction instance.
            edition_url (str): The edition URL.
            precta (bool): Whether to include pre CTA. Defaults to False.
            postcta (bool): Whether to include post CTA. Defaults to False.
            thread (bool): Whether to create a thread. Defaults to False.
        """
        try:
            user_config = load_user_config(key)
            await run_script_command(
                interaction,
                edition_url,
                precta,
                postcta,
                thread,
                user_config,
                key,
                config,
            )
        except Exception as e:
            logging.exception("Error during run_script command:")
            await interaction.response.send_message(
                "Failed to run the script. Please try again later.", ephemeral=True
            )

    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    logging.info("Starting the Discord bot...")
    run_discord_bot({}, b"some_key")
