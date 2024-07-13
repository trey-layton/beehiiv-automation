from typing import Optional
import discord
from discord import app_commands
from tweepy.errors import TweepyException
from core.main_process import run_main_process
from core.config.user_config import load_user_config, save_user_config, get_key
from core.config.feature_toggle import feature_toggle
from requests_oauthlib import OAuth1Session
import asyncio
import logging
import os
import json
from core.social_media.twitter.tweet_handler import TweetHandler
from .admin_commands import (
    debug_encryption_key,
    reset_user_config,
    delete_user,
    debug_user_config,
    list_users,
    toggle_feature,
    list_features,
)
from discord.ui import Button, View

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
USER_CONFIG_PATH = os.path.join(PROJECT_ROOT, "user_config.db")

ADMIN_USER_ID = "795075580659236904"  # Replace with your Discord user ID


def is_admin(interaction: discord.Interaction) -> bool:
    return str(interaction.user.id) == ADMIN_USER_ID


class ConfirmView(discord.ui.View):
    def __init__(self, tweets, user_id, edition_url, twitter_credentials):
        super().__init__()
        self.tweets = tweets
        self.user_id = user_id
        self.edition_url = edition_url
        self.tweet_handler = TweetHandler(twitter_credentials)
        self.tweet_handler.set_user_id(user_id)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        results = []
        try:
            # Initialize Twitter OAuth
            try:
                self.tweet_handler.initialize_twitter_oauth()
                logger.info("Twitter OAuth initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter OAuth: {str(e)}")
                await interaction.followup.send(
                    f"Failed to initialize Twitter OAuth: {str(e)}"
                )
                return

            for tweet_type, tweet_data in self.tweets.items():
                try:
                    if tweet_type == "precta":
                        tweet_id = await self.tweet_handler.post_tweet(
                            tweet_data["text"]
                        )
                        if tweet_id:
                            reply_id = await self.tweet_handler.post_tweet(
                                tweet_data["reply"], in_reply_to_tweet_id=tweet_id
                            )
                            results.append(
                                f"Pre-CTA tweet posted successfully. Tweet ID: {tweet_id}, Reply ID: {reply_id}"
                            )
                        else:
                            results.append("Failed to post Pre-CTA tweet")
                    elif tweet_type == "postcta":
                        media_id = await self.tweet_handler.upload_media(
                            tweet_data["media_url"]
                        )
                        tweet_id = await self.tweet_handler.post_tweet(
                            tweet_data["text"], media_id=media_id
                        )
                        if tweet_id:
                            reply_id = await self.tweet_handler.post_tweet(
                                tweet_data["reply"], in_reply_to_tweet_id=tweet_id
                            )
                            results.append(
                                f"Post-CTA tweet posted successfully. Tweet ID: {tweet_id}, Reply ID: {reply_id}"
                            )
                        else:
                            results.append("Failed to post Post-CTA tweet")
                    elif tweet_type == "thread":
                        await self.tweet_handler.post_thread(
                            tweet_data, self.edition_url
                        )
                        results.append("Thread posted successfully")
                except Exception as e:
                    logger.error(f"Error posting {tweet_type} tweet: {str(e)}")
                    results.append(f"Error posting {tweet_type} tweet: {str(e)}")

            await interaction.followup.send("\n".join(results))
        except Exception as e:
            logger.error(f"An unexpected error occurred while posting tweets: {str(e)}")
            await interaction.followup.send(
                f"An unexpected error occurred while posting tweets: {str(e)}"
            )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Tweet posting cancelled.")
        self.stop()


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, config):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.config = config

    async def setup_hook(self):
        await self.tree.sync()


def run_discord_bot(config):
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents, config=config)

    config.update(
        {
            "twitter_api_key": os.getenv("TWITTER_API_KEY"),
            "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
        }
    )

    @client.tree.command()
    @app_commands.check(is_admin)
    async def admin(interaction: discord.Interaction):
        if not is_admin(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        user = interaction.user
        await user.send(
            "Please enter the operation you want to perform:\n"
            "1. Reset user config\n"
            "2. Delete user\n"
            "3. Debug user config\n"
            "4. List users\n"
            "5. Sync commands\n"
            "6. Toggle feature\n"
            "7. List features\n"
            "8. Debug encryption key"
        )

        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)

        try:
            operation_msg = await client.wait_for("message", check=check, timeout=60.0)
            operation = operation_msg.content.lower()

            result = "Invalid operation."

            if operation == "1":
                await user.send("Enter the user ID to reset:")
                user_id_msg = await client.wait_for(
                    "message", check=check, timeout=60.0
                )
                result = await reset_user_config(user_id_msg.content)
            elif operation == "2":
                await user.send("Enter the user ID to delete:")
                user_id_msg = await client.wait_for(
                    "message", check=check, timeout=60.0
                )
                result = await delete_user(user_id_msg.content)
            elif operation == "3":
                await user.send("Enter the user ID to debug:")
                user_id_msg = await client.wait_for(
                    "message", check=check, timeout=60.0
                )
                result = await debug_user_config(user_id_msg.content)
            elif operation == "4":
                result = await list_users()
            elif operation == "5":
                await client.tree.sync()
                result = "Command tree synced."
            elif operation == "6":
                await user.send("Enter the feature name:")
                feature_name = await client.wait_for(
                    "message", check=check, timeout=60.0
                )
                await user.send("Enter 'enable' or 'disable':")
                enable_msg = await client.wait_for("message", check=check, timeout=60.0)
                enable = enable_msg.content.lower() == "enable"
                result = toggle_feature(feature_name.content, enable)
            elif operation == "7":
                result = list_features()
            elif operation == "8":
                result = await debug_encryption_key()

            await user.send(result)
            await interaction.followup.send(
                "Operation completed. Check your DMs for the result.", ephemeral=True
            )
        except asyncio.TimeoutError:
            await user.send("Operation timed out. Please try again.")
            await interaction.followup.send(
                "Operation timed out. Please try again.", ephemeral=True
            )
        except Exception as e:
            logger.exception("Error in admin command:")
            await user.send(f"An error occurred: {str(e)}")
            await interaction.followup.send(
                "An error occurred. Check your DMs for details.", ephemeral=True
            )

    @admin.error
    async def admin_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.errors.CheckFailure):
            await interaction.response.send_message(
                f"You don't have permission to use this command. Your user ID: {interaction.user.id}",
                ephemeral=True,
            )
        else:
            logger.error(f"Error in admin command: {str(error)}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"An error occurred: {str(error)}", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"An error occurred: {str(error)}", ephemeral=True
                )

    @client.tree.command()
    async def register(
        interaction: discord.Interaction,
        email: str,
        password: str,
        confirm_password: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            if password != confirm_password:
                await interaction.followup.send(
                    "Passwords do not match. Please try again.", ephemeral=True
                )
                return

            user_id = str(interaction.user.id)
            logger.info(f"Registering user: {user_id}")
            user_config = load_user_config(user_id) or {}
            logger.info(f"Loaded user config: {user_config}")
            user_config.update({"email": email, "password": password})
            logger.info(f"Updated user config: {user_config}")
            success = save_user_config(user_config, user_id)

            if success:
                logger.info(f"Registration successful for user: {user_id}")
                await interaction.followup.send(
                    "Registration successful! Please use the /update_profile command to add your Beehiiv information, and the /authorize_twitter command to link your Twitter account.",
                    ephemeral=True,
                )
            else:
                logger.error(f"Registration failed for user: {user_id}")
                await interaction.followup.send(
                    "Registration failed. Please try again.", ephemeral=True
                )
        except Exception as e:
            logger.exception(f"An error occurred during registration: {str(e)}")
            await interaction.followup.send(
                "An error occurred during registration. Please try again later.",
                ephemeral=True,
            )

    @client.tree.command()
    async def update_profile(
        interaction: discord.Interaction,
        beehiiv_api_key: str,
        subscribe_url: str,
        publication_id: str,
        example_tweet: str = None,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            user_id = str(interaction.user.id)
            user_config = load_user_config(user_id) or {}

            user_config.update(
                {
                    "beehiiv_api_key": beehiiv_api_key,
                    "subscribe_url": subscribe_url,
                    "publication_id": publication_id,
                }
            )

            if example_tweet:
                user_config["example_tweet"] = example_tweet

            success = save_user_config(user_config, user_id)

            if success:
                await interaction.followup.send(
                    "Profile updated successfully!", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An error occurred while updating your profile. Please try again later.",
                    ephemeral=True,
                )

            if (
                "twitter_access_key" not in user_config
                or "twitter_access_secret" not in user_config
            ):
                await interaction.followup.send(
                    "Don't forget to authorize your Twitter account using the /authorize_twitter command.",
                    ephemeral=True,
                )
        except Exception as e:
            logger.exception(f"An error occurred while updating profile: {str(e)}")
            await interaction.followup.send(
                "An error occurred while updating your profile. Please try again later.",
                ephemeral=True,
            )

    @client.tree.command()
    async def authorize_twitter(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            user_id = str(interaction.user.id)
            user_config = load_user_config(user_id) or {}

            logger.info(f"Authorizing Twitter for user: {user_id}")
            logger.debug(f"Current user config: {user_config}")

            twitter_consumer_key = os.getenv("TWITTER_API_KEY")
            twitter_consumer_secret = os.getenv("TWITTER_API_SECRET")

            if not twitter_consumer_key or not twitter_consumer_secret:
                await interaction.followup.send(
                    "Twitter API credentials are not properly configured. Please contact the administrator.",
                    ephemeral=True,
                )
                return

            oauth = OAuth1Session(
                twitter_consumer_key,
                client_secret=twitter_consumer_secret,
                callback_uri="oob",
            )

            try:
                request_token_response = oauth.fetch_request_token(
                    "https://api.twitter.com/oauth/request_token"
                )
            except Exception as e:
                logger.error(f"Failed to fetch request token: {e}")
                await interaction.followup.send(
                    "Failed to initiate Twitter authorization. Please try again later.",
                    ephemeral=True,
                )
                return

            authorization_url = oauth.authorization_url(
                "https://api.twitter.com/oauth/authorize"
            )
            user_config.update(
                {
                    "oauth_token": request_token_response.get("oauth_token"),
                    "oauth_token_secret": request_token_response.get(
                        "oauth_token_secret"
                    ),
                }
            )

            logger.debug(f"User config before saving: {user_config}")
            success = save_user_config(user_config, user_id)

            if success:
                await interaction.followup.send(
                    f"Please authorize the bot by visiting this URL: {authorization_url}\n"
                    "After authorization, you will receive a PIN. Use the /confirm_auth command with this PIN to complete the process.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "An error occurred while saving your configuration. Please try again.",
                    ephemeral=True,
                )

        except Exception as e:
            logger.exception(f"Failed to initiate Twitter OAuth: {str(e)}")
            await interaction.followup.send(
                f"Failed to initiate Twitter OAuth: {str(e)}", ephemeral=True
            )

    @client.tree.command()
    @app_commands.describe(pin="The PIN provided by Twitter after authorization")
    async def confirm_auth(interaction: discord.Interaction, pin: str):
        await interaction.response.defer(ephemeral=True)

        try:
            user_id = str(interaction.user.id)
            user_config = load_user_config(user_id)

            logger.info(f"Confirming auth for user: {user_id}")
            logger.debug(f"Current user config: {user_config}")

            if not user_config or not isinstance(user_config, dict):
                logger.warning(
                    f"User {user_id} not found in config or config is not a dict"
                )
                await interaction.followup.send(
                    "Please use the /authorize_twitter command first.", ephemeral=True
                )
                return

            twitter_consumer_key = os.getenv("TWITTER_API_KEY")
            twitter_consumer_secret = os.getenv("TWITTER_API_SECRET")
            oauth_token = user_config.get("oauth_token")
            oauth_token_secret = user_config.get("oauth_token_secret")

            if not oauth_token or not oauth_token_secret:
                logger.warning(f"OAuth tokens not found for user {user_id}")
                await interaction.followup.send(
                    "Please use the /authorize_twitter command first.", ephemeral=True
                )
                return

            oauth = OAuth1Session(
                twitter_consumer_key,
                client_secret=twitter_consumer_secret,
                resource_owner_key=oauth_token,
                resource_owner_secret=oauth_token_secret,
                verifier=pin,
            )

            try:
                access_token_response = oauth.fetch_access_token(
                    "https://api.twitter.com/oauth/access_token"
                )
            except Exception as e:
                logger.error(f"Failed to fetch access token: {e}")
                await interaction.followup.send(
                    "Failed to complete Twitter authorization. Please try the process again.",
                    ephemeral=True,
                )
                return

            user_config["twitter_access_key"] = access_token_response.get("oauth_token")
            user_config["twitter_access_secret"] = access_token_response.get(
                "oauth_token_secret"
            )

            logger.debug(f"Updated user config before saving: {user_config}")
            success = save_user_config(user_config, user_id)

            if success:
                await interaction.followup.send(
                    "Twitter account successfully linked!", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An error occurred while saving your Twitter credentials. Please try again.",
                    ephemeral=True,
                )

        except Exception as e:
            logger.exception(f"Error during Twitter authentication: {str(e)}")
            await interaction.followup.send(
                f"An error occurred during authentication: {str(e)}", ephemeral=True
            )

    @client.tree.command()
    @app_commands.describe(
        edition_url="URL of the specific edition to fetch content for",
        precta="Generate pre-newsletter CTA tweet",
        postcta="Generate post-newsletter CTA tweet",
        thread="Generate thread tweets",
        long_form="Generate a long-form tweet (approximately 850 characters)",
        linkedin="Generate a LinkedIn post",
    )
    async def generate_content(
        interaction: discord.Interaction,
        edition_url: str,
        precta: Optional[bool] = False,
        postcta: Optional[bool] = False,
        thread: Optional[bool] = False,
        long_form: Optional[bool] = False,
        linkedin: Optional[bool] = False,
    ):
        await interaction.response.defer(thinking=True)
        try:
            user_id = str(interaction.user.id)
            result = await run_main_process(
                user_id, edition_url, precta, postcta, thread, long_form, linkedin
            )

            if len(result) != 3:
                logger.error(f"Unexpected result from run_main_process: {result}")
                await interaction.followup.send(
                    "An unexpected error occurred. Please try again later."
                )
                return

            success, message, generated_content = result

            if success:
                if not generated_content:
                    await interaction.followup.send(
                        "No content was generated as no options were selected. Please select at least one type of content to generate."
                    )
                else:
                    response = "Generated Content:\n\n"
                    for content_type, content_data in generated_content.items():
                        response += f"{content_type.upper()}:\n"
                        if isinstance(content_data, dict):
                            content_text = content_data["text"]
                            if content_type in ["long_form", "linkedin"]:
                                content_text = content_text.replace("<br>", "\n\n")
                                content_text = content_text.strip()
                            response += f"Content:\n{content_text}\n"
                            if "reply" in content_data:
                                response += f"Reply: {content_data['reply']}\n"
                        elif isinstance(content_data, list):
                            if content_data:  # Check if the list is not empty
                                for i, tweet in enumerate(content_data, 1):
                                    response += f"Tweet {i}: {tweet}\n"
                            else:
                                response += "No tweets were generated.\n"
                        else:
                            if content_type in ["long_form", "linkedin"]:
                                content_data = content_data.replace("<br>", "\n\n")
                                content_data = content_data.strip()
                            response += f"{content_data}\n"
                        response += "\n"

                    # Send the response in chunks if it's too long
                    if len(response) > 2000:
                        chunks = [
                            response[i : i + 1990]
                            for i in range(0, len(response), 1990)
                        ]
                        for chunk in chunks:
                            await interaction.followup.send(chunk)
                    else:
                        await interaction.followup.send(response)

                    # Only show the confirmation view for tweets that can be posted automatically
                    if precta or postcta or thread:
                        user_config = load_user_config(user_id)
                        twitter_credentials = {
                            "twitter_api_key": os.getenv("TWITTER_API_KEY"),
                            "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
                            "twitter_access_key": user_config.get("twitter_access_key"),
                            "twitter_access_secret": user_config.get(
                                "twitter_access_secret"
                            ),
                        }
                        view = ConfirmView(
                            generated_content, user_id, edition_url, twitter_credentials
                        )
                        await interaction.followup.send(
                            "Do you want to post these tweets?", view=view
                        )
            else:
                await interaction.followup.send(f"An error occurred: {message}")
        except Exception as e:
            logger.error(f"Generate content error: {str(e)}")
            await interaction.followup.send(
                f"An unexpected error occurred while generating content: {str(e)}"
            )

    return client
