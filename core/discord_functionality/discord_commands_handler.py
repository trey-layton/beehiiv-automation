import discord
from requests_oauthlib import OAuth1Session
from typing import Dict, Any
import logging
import os
import subprocess
from core.discord_functionality.discord_utils import save_user_config


async def set_config_command(
    interaction: discord.Interaction,
    beehiiv_api_key: str,
    subscribe_url: str,
    publication_id: str,
    user_config: Dict[str, Dict[str, Any]],
    key: bytes,
    config: Dict[str, Any],
) -> None:
    """
    Command to set user configuration.
    """
    user = str(interaction.user)
    twitter_consumer_key = config["twitter_api_key"]
    twitter_consumer_secret = config["twitter_api_secret"]

    if user not in user_config:
        user_config[user] = {}

    user_config[user].update(
        {
            "beehiiv_api_key": beehiiv_api_key,
            "subscribe_url": subscribe_url,
            "publication_id": publication_id,
        }
    )

    oauth = OAuth1Session(
        twitter_consumer_key, client_secret=twitter_consumer_secret, callback_uri="oob"
    )

    try:
        request_token_response = oauth.fetch_request_token(
            "https://api.twitter.com/oauth/request_token"
        )
        authorization_url = oauth.authorization_url(
            "https://api.twitter.com/oauth/authorize"
        )

        user_config[user].update(
            {
                "oauth_token": request_token_response.get("oauth_token"),
                "oauth_token_secret": request_token_response.get("oauth_token_secret"),
            }
        )

        save_user_config(user_config, key)

        await interaction.response.send_message(
            f"Configuration saved for {user}. Please authorize the bot by visiting: {authorization_url}"
        )

        await interaction.followup.send(
            "Please enter the PIN code from Twitter authorization."
        )
    except Exception as e:
        logging.error(f"Failed to initiate Twitter OAuth: {e}")
        await interaction.response.send_message(
            f"Failed to initiate Twitter OAuth: {e}"
        )


async def run_script_command(
    interaction: discord.Interaction,
    edition_url: str,
    precta: bool,
    postcta: bool,
    thread: bool,
    user_config: Dict[str, Dict[str, Any]],
    key: bytes,
    config: Dict[str, Any],
) -> None:
    """
    Command to run the main script.
    """
    await interaction.response.defer()  # Defer the interaction response
    user = str(interaction.user)
    if user not in user_config or "twitter_access_key" not in user_config[user]:
        await interaction.followup.send(
            f"No configuration or Twitter authorization found for {user}. Please use /set_config and /authorize_twitter to set it up."
        )
        return

    user_conf = user_config[user]
    twitter_consumer_key = config["twitter_api_key"]
    twitter_consumer_secret = config["twitter_api_secret"]

    twitter_oauth = OAuth1Session(
        twitter_consumer_key,
        client_secret=twitter_consumer_secret,
        resource_owner_key=user_conf["twitter_access_key"],
        resource_owner_secret=user_conf["twitter_access_secret"],
    )

    script_path = os.path.join(os.getcwd(), "main.py")
    command = ["python3", script_path, user, edition_url]
    if precta:
        command.append("--precta")
    if postcta:
        command.append("--postcta")
    if thread:
        command.append("--thread")

    try:
        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),  # Ensure the working directory is correct
        )
        if result.returncode == 0:
            await interaction.followup.send(f"Successfully ran the script for {user}.")
            logging.info(f"Script output: {result.stdout}")
        else:
            await interaction.followup.send(
                f"Error running the script: {result.stderr}"
            )
            logging.error(f"Script error: {result.stderr}")
    except Exception as e:
        logging.error(f"Exception while running the script: {e}")
        await interaction.followup.send(f"Error running the script: {str(e)}")
