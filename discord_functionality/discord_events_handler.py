import discord
import logging
from discord_functionality.discord_utils import save_user_config
from requests_oauthlib import OAuth1Session
from typing import Dict, Any


async def on_ready(bot: discord.ext.commands.Bot, config: Dict[str, str]) -> None:
    """
    Event handler for when the bot is ready.

    Args:
        bot (discord.ext.commands.Bot): The Discord bot instance.
        config (Dict[str, str]): The configuration dictionary.
    """
    logging.info(f"Logged in as {bot.user}!")
    guild_id = config["guild_id"]
    guild = discord.Object(id=guild_id)
    try:
        await bot.tree.sync(guild=guild)
        logging.info("Command tree synced.")
        logging.info("Registered commands:")
        for command in bot.tree.walk_commands():
            logging.info(f"- {command.name}")
    except Exception as e:
        logging.error(f"Failed to sync command tree: {e}")


async def on_message(
    bot: discord.ext.commands.Bot,
    message: discord.Message,
    user_config: Dict[str, Dict[str, Any]],
    key: bytes,
    config: Dict[str, str],
) -> None:
    """
    Event handler for receiving messages.

    Args:
        bot (discord.ext.commands.Bot): The Discord bot instance.
        message (discord.Message): The message received.
        user_config (Dict[str, Dict[str, Any]]): The user configuration.
        key (bytes): The encryption key.
        config (Dict[str, str]): The configuration dictionary.
    """
    if message.author == bot.user:
        return

    if (
        message.content.isdigit() and len(message.content) == 7
    ):  # Assuming PIN is 7 digits
        pin_code = message.content

        user = str(message.author)
        user_conf = user_config.get(user)
        if not user_conf:
            await message.channel.send(
                f"No configuration found for {user}. Please use /set_config to set it up."
            )
            return

        oauth = OAuth1Session(
            config["twitter_api_key"],
            client_secret=config["twitter_api_secret"],
            resource_owner_key=user_conf["oauth_token"],
            resource_owner_secret=user_conf["oauth_token_secret"],
            verifier=pin_code,
        )

        try:
            access_token_response = oauth.fetch_access_token(
                "https://api.twitter.com/oauth/access_token"
            )

            user_conf.update(
                {
                    "twitter_access_key": access_token_response.get("oauth_token"),
                    "twitter_access_secret": access_token_response.get(
                        "oauth_token_secret"
                    ),
                }
            )

            user_config[user] = user_conf
            save_user_config(user_config, key)

            await message.channel.send(f"Twitter account authorized for {user}.")
        except Exception as e:
            logging.error(f"Error authorizing Twitter account for {user}: {e}")
            await message.channel.send(f"Error authorizing Twitter account: {str(e)}")
