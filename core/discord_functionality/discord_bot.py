import discord
from discord import app_commands
from tweepy.errors import TweepyException
from core.main_process import run_main_process
from core.config.user_config import (
    save_user_config,
    load_user_config,
    update_twitter_tokens,
)
import tweepy
import asyncio
import logging

logger = logging.getLogger(__name__)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, config, key):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.temp_user_data = {}
        self.config = config
        self.key = key
        self.oauth1_user_handler = tweepy.OAuthHandler(
            config["twitter_api_key"], config["twitter_api_secret"], callback="oob"
        )

    async def setup_hook(self):
        await self.tree.sync()


def run_discord_bot(config, key):
    intents = discord.Intents.default()
    client = MyClient(intents=intents, config=config, key=key)

    @client.tree.command()
    @app_commands.describe(
        beehiiv_api_key="Your Beehiiv API key",
        beehiiv_publication_id="Your Beehiiv publication ID",
        subscribe_url="Your unique Beehiiv subscribe URL",
    )
    async def register(
        interaction: discord.Interaction,
        beehiiv_api_key: str,
        beehiiv_publication_id: str,
        subscribe_url: str,
    ):
        await interaction.response.defer(ephemeral=True)

        try:
            auth_url = client.oauth1_user_handler.get_authorization_url()

            client.temp_user_data[interaction.user.id] = {
                "beehiiv_api_key": beehiiv_api_key,
                "beehiiv_publication_id": beehiiv_publication_id,
                "subscribe_url": subscribe_url,
            }

            await interaction.followup.send(
                f"Please visit this URL to authorize the app: {auth_url}\n"
                "After authorizing, you will receive a PIN. Use the /confirm_auth command with this PIN.",
                ephemeral=True,
            )
        except TweepyException as e:
            logger.error(f"Twitter API error in register command: {e}")
            await interaction.followup.send(
                f"Error! Failed to get request token: {str(e)}", ephemeral=True
            )
        except Exception as e:
            logger.exception(f"Unexpected error in register command: {e}")
            await interaction.followup.send(
                f"An unexpected error occurred: {str(e)}", ephemeral=True
            )

    @client.tree.command()
    @app_commands.describe(pin="The PIN provided by Twitter after authorization")
    async def confirm_auth(interaction: discord.Interaction, pin: str):
        await interaction.response.defer(ephemeral=True)

        try:
            client.oauth1_user_handler.get_access_token(pin)
            access_token = client.oauth1_user_handler.access_token
            access_token_secret = client.oauth1_user_handler.access_token_secret

            beehiiv_info = client.temp_user_data.get(interaction.user.id, {})

            user_config = {
                "discord_username": f"{interaction.user.name}#{interaction.user.discriminator}",
                "twitter_access_key": access_token,
                "twitter_access_secret": access_token_secret,
                "beehiiv_api_key": beehiiv_info.get("beehiiv_api_key"),
                "beehiiv_publication_id": beehiiv_info.get("beehiiv_publication_id"),
                "subscribe_url": beehiiv_info.get("subscribe_url"),
            }

            logger.info(
                f"Attempting to save user config for user {interaction.user.id}"
            )
            success = save_user_config(
                user_config, client.key, str(interaction.user.id)
            )

            if success:
                logger.info(
                    f"User config saved successfully for user {interaction.user.id}"
                )
                await interaction.followup.send(
                    "Authentication successful! Your account is now registered.",
                    ephemeral=True,
                )
                client.temp_user_data.pop(interaction.user.id, None)
            else:
                logger.error(
                    f"Failed to save user config for user {interaction.user.id}"
                )
                await interaction.followup.send(
                    "Failed to save user configuration. Please try again.",
                    ephemeral=True,
                )
        except TweepyException as e:
            logger.error(f"Twitter API error in confirm_auth command: {e}")
            await interaction.followup.send(
                f"Error! Failed to get access token: {str(e)}", ephemeral=True
            )
        except Exception as e:
            logger.exception(f"Unexpected error in confirm_auth command: {e}")
            await interaction.followup.send(
                f"An unexpected error occurred: {str(e)}", ephemeral=True
            )

    @client.tree.command()
    @app_commands.describe(
        edition_url="URL of the specific edition to fetch content for",
        precta="Generate pre-newsletter CTA tweet",
        postcta="Generate post-newsletter CTA tweet",
        thread="Generate thread tweets",
    )
    async def generate_tweets(
        interaction: discord.Interaction,
        edition_url: str,
        precta: bool = False,
        postcta: bool = False,
        thread: bool = False,
    ):
        logger.info(f"generate_tweets command invoked by user {interaction.user.id}")
        logger.info(
            f"Parameters: edition_url={edition_url}, precta={precta}, postcta={postcta}, thread={thread}"
        )

        try:
            # Attempt to defer the response immediately
            await interaction.response.defer(thinking=True)
            logger.info("Interaction deferred successfully")
        except discord.errors.NotFound:
            logger.warning(
                f"Interaction {interaction.id} has expired. Unable to defer response."
            )
            return  # Exit the function as we can't respond to an expired interaction

        try:
            logger.info("Preparing to run main process")
            key_path = "core/config/secret.key"
            user_config_path = "user_config.db"

            # Run the main process in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                run_main_process,
                str(interaction.user.id),
                edition_url,
                precta,
                postcta,
                thread,
                key_path,
                user_config_path,
            )

            logger.info(f"Main process result: {result}")

            if result is None:
                raise ValueError("run_main_process returned None")

            success, message = result
            logger.info(f"Process completed. Success: {success}, Message: {message}")

            if success:
                await interaction.followup.send(
                    "Tweets generated and posted successfully!"
                )
            else:
                if "Twitter authentication failed" in message:
                    # Handle Twitter authentication failure
                    logger.error("Twitter authentication failed")
                    auth_url = client.oauth1_user_handler.get_authorization_url()
                    client.temp_user_data[interaction.user.id] = {
                        "reauth": True,
                    }
                    await interaction.followup.send(
                        f"Your Twitter tokens are invalid. Please reauthorize by visiting this URL: {auth_url}\n"
                        "After authorizing, use the /confirm_auth command with the new PIN.",
                        ephemeral=True,
                    )
                else:
                    logger.error(f"Tweet generation failed: {message}")
                    await interaction.followup.send(
                        f"An error occurred while generating and posting tweets: {message}"
                    )
        except Exception as e:
            logger.exception(f"Unexpected error in generate_tweets command: {e}")
            await interaction.followup.send(
                "An unexpected error occurred. Please check the logs for more information."
            )

    return client
