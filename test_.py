import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from discord.ext import commands
from discord import Intents, Interaction, app_commands
from typing import Dict, Any
import os
from discord_functionality.discord_bot import run_discord_bot


class TestDiscordBot(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.config = {
            "discord_bot_token": "test_token",
            "twitter_api_key": "test_twitter_api_key",
            "twitter_api_secret": "test_twitter_api_secret",
            "discord_bot_token": os.getenv("DISCORD_BOT_TOKEN", "test_token"),
        }
        self.key = b"test_key"

    @patch("discord.ext.commands.Bot.run")
    @patch("discord_functionality.discord_bot.load_user_config", return_value={})
    @patch("discord_functionality.discord_bot.on_ready", new_callable=AsyncMock)
    @patch("discord_functionality.discord_bot.on_message", new_callable=AsyncMock)
    @patch(
        "discord_functionality.discord_bot.set_config_command", new_callable=AsyncMock
    )
    @patch(
        "discord_functionality.discord_bot.run_script_command", new_callable=AsyncMock
    )
    async def test_run_discord_bot(
        self,
        mock_run_script_command,
        mock_set_config_command,
        mock_on_message,
        mock_on_ready,
        mock_load_user_config,
        mock_bot_run,
    ):
        # Initialize and run the bot
        run_discord_bot(self.config, self.key)

        # Check if bot.run was called
        mock_bot_run.assert_called_once_with(self.config["discord_bot_token"])

    @patch("discord.ext.commands.Bot.run")
    @patch("discord_functionality.discord_bot.load_user_config", return_value={})
    @patch("discord_functionality.discord_bot.on_ready", new_callable=AsyncMock)
    @patch("discord_functionality.discord_bot.on_message", new_callable=AsyncMock)
    async def test_on_ready_event(
        self, mock_on_message, mock_on_ready, mock_load_user_config, mock_bot_run
    ):
        # Mock bot instance
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready_event():
            await mock_on_ready(bot, self.config)

        # Simulate on_ready event
        await on_ready_event()
        mock_on_ready.assert_awaited_once_with(bot, self.config)

    @patch("discord.ext.commands.Bot.run")
    @patch("discord_functionality.discord_bot.load_user_config", return_value={})
    @patch("discord_functionality.discord_bot.on_message", new_callable=AsyncMock)
    async def test_on_message_event(
        self, mock_on_message, mock_load_user_config, mock_bot_run
    ):
        # Mock bot instance
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_message_event(message):
            await mock_on_message(bot, message, {}, self.key, self.config)

        # Simulate on_message event
        message = MagicMock()
        await on_message_event(message)
        mock_on_message.assert_awaited_once_with(
            bot, message, {}, self.key, self.config
        )

    @patch("discord.ext.commands.Bot.run")
    @patch("discord_functionality.discord_bot.load_user_config", return_value={})
    @patch(
        "discord_functionality.discord_bot.set_config_command", new_callable=AsyncMock
    )
    async def test_set_config_command(
        self, mock_set_config_command, mock_load_user_config, mock_bot_run
    ):
        # Mock bot instance
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.tree.command(name="set_config", description="Set user configuration")
        @app_commands.describe(
            beehiiv_api_key="Your Beehiiv API key",
            subscribe_url="Your subscribe URL",
            publication_id="Your publication ID",
        )
        async def set_config(
            interaction: Interaction,
            beehiiv_api_key: str,
            subscribe_url: str,
            publication_id: str,
        ):
            await mock_set_config_command(
                interaction,
                beehiiv_api_key,
                subscribe_url,
                publication_id,
                {},
                self.key,
                self.config,
            )
            await interaction.response.send_message(
                f"Set config: {beehiiv_api_key}, {subscribe_url}, {publication_id}",
                ephemeral=True,
            )

        # Simulate set_config command
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        command = bot.tree.get_command("set_config")
        await command.callback(
            interaction,
            beehiiv_api_key="test_api_key",
            subscribe_url="test_subscribe_url",
            publication_id="test_publication_id",
        )
        mock_set_config_command.assert_awaited_once_with(
            interaction,
            "test_api_key",
            "test_subscribe_url",
            "test_publication_id",
            {},
            self.key,
            self.config,
        )
        interaction.response.send_message.assert_awaited_once_with(
            "Set config: test_api_key, test_subscribe_url, test_publication_id",
            ephemeral=True,
        )

    @patch("discord.ext.commands.Bot.run")
    @patch("discord_functionality.discord_bot.load_user_config", return_value={})
    @patch(
        "discord_functionality.discord_bot.run_script_command", new_callable=AsyncMock
    )
    async def test_run_script_command(
        self, mock_run_script_command, mock_load_user_config, mock_bot_run
    ):
        # Mock bot instance
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.tree.command(name="run_script", description="Run the main script")
        @app_commands.describe(
            edition_url="Edition URL",
            precta="Include pre CTA",
            postcta="Include post CTA",
            thread="Create a thread",
        )
        async def run_script(
            interaction: Interaction,
            edition_url: str,
            precta: bool = False,
            postcta: bool = False,
            thread: bool = False,
        ):
            await mock_run_script_command(
                interaction,
                edition_url,
                precta,
                postcta,
                thread,
                {},
                self.key,
                self.config,
            )
            await interaction.response.send_message(
                f"Run script: {edition_url}, precta={precta}, postcta={postcta}, thread={thread}",
                ephemeral=True,
            )

        # Simulate run_script command
        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()

        command = bot.tree.get_command("run_script")
        await command.callback(
            interaction,
            edition_url="test_edition_url",
            precta=True,
            postcta=True,
            thread=True,
        )
        mock_run_script_command.assert_awaited_once_with(
            interaction,
            "test_edition_url",
            True,
            True,
            True,
            {},
            self.key,
            self.config,
        )
        interaction.response.send_message.assert_awaited_once_with(
            "Run script: test_edition_url, precta=True, postcta=True, thread=True",
            ephemeral=True,
        )


if __name__ == "__main__":
    unittest.main()
