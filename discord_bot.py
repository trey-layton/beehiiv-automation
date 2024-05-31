import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import subprocess
from requests_oauthlib import OAuth1Session
from cryptography.fernet import Fernet
import base64
from config import get_config

# Load environment variables and configuration
config = get_config()

# Get the bot token and application ID from environment variables
DISCORD_BOT_TOKEN = config["discord_bot_token"]
DISCORD_APP_ID = config["discord_app_id"]
GUILD_ID = config["guild_id"]
TWITTER_CONSUMER_KEY = config["twitter_api_key"]
TWITTER_CONSUMER_SECRET = config["twitter_api_secret"]

if (
    not DISCORD_BOT_TOKEN
    or not DISCORD_APP_ID
    or not GUILD_ID
    or not TWITTER_CONSUMER_KEY
    or not TWITTER_CONSUMER_SECRET
):
    raise ValueError("All environment variables must be set")

user_config_path = "user_config.enc"
key_path = "secret.key"  # Define key_path here


def generate_key():
    return Fernet.generate_key()


def save_key(key, path):
    with open(path, "wb") as key_file:
        key_file.write(key)


def load_key(path):
    if not os.path.exists(path):
        key = generate_key()
        save_key(key, path)
    else:
        with open(path, "rb") as key_file:
            key = key_file.read()
    return key


def encrypt_data(data, key):
    cipher_suite = Fernet(key)
    json_data = json.dumps(data).encode()
    encrypted_data = cipher_suite.encrypt(json_data)
    return base64.b64encode(encrypted_data).decode("utf-8")  # Convert to string


def decrypt_data(encrypted_data, key):
    cipher_suite = Fernet(key)
    encrypted_data = base64.b64decode(
        encrypted_data.encode("utf-8")
    )  # Convert to bytes
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())


def save_user_config(user_config, key):
    encrypted_data = {}
    for user, config in user_config.items():
        encrypted_data[user] = encrypt_data(config, key)
    with open(user_config_path, "w") as file:
        json.dump(encrypted_data, file)


def load_user_config(key):
    if not os.path.exists(user_config_path):
        return {}
    with open(user_config_path, "r") as file:
        try:
            encrypted_data = json.load(file)
        except json.JSONDecodeError:
            return {}
    user_config = {}
    for user, encrypted_config in encrypted_data.items():
        user_config[user] = decrypt_data(encrypted_config, key)
    return user_config


key = load_key(key_path)
user_config = load_user_config(key)

# Create a bot instance
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)  # Sync the command to the specific guild
    print("Command tree synced.")

    # Print all registered commands
    print("Registered commands:")
    for command in bot.tree.walk_commands():
        print(f"- {command.name}")


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
):
    user = str(interaction.user)

    if user not in user_config:
        user_config[user] = {}

    user_config[user].update(
        {
            "beehiiv_api_key": beehiiv_api_key,
            "subscribe_url": subscribe_url,
            "publication_id": publication_id,
        }
    )

    # Start Twitter OAuth process
    oauth = OAuth1Session(
        TWITTER_CONSUMER_KEY, client_secret=TWITTER_CONSUMER_SECRET, callback_uri="oob"
    )

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

    # Send initial response promptly
    await interaction.response.send_message(
        f"Configuration saved for {user}. Please authorize the bot by visiting: {authorization_url}"
    )

    # Follow-up message to enter the PIN
    await interaction.followup.send(
        "Please enter the PIN code from Twitter authorization."
    )

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        if (
            message.content.isdigit() and len(message.content) == 7
        ):  # Assuming PIN is 7 digits
            pin_code = message.content

            config = user_config.get(user)
            if not config:
                await message.channel.send(
                    f"No configuration found for {user}. Please use /set_config to set it up."
                )
                return

            oauth = OAuth1Session(
                TWITTER_CONSUMER_KEY,
                client_secret=TWITTER_CONSUMER_SECRET,
                resource_owner_key=config["oauth_token"],
                resource_owner_secret=config["oauth_token_secret"],
                verifier=pin_code,
            )

            try:
                access_token_response = oauth.fetch_access_token(
                    "https://api.twitter.com/oauth/access_token"
                )

                config.update(
                    {
                        "twitter_access_key": access_token_response.get("oauth_token"),
                        "twitter_access_secret": access_token_response.get(
                            "oauth_token_secret"
                        ),
                    }
                )

                user_config[user] = config
                save_user_config(user_config, key)

                await message.channel.send(f"Twitter account authorized for {user}.")
            except Exception as e:
                await message.channel.send(
                    f"Error authorizing Twitter account: {str(e)}"
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
):
    await interaction.response.defer()  # Defer the interaction response
    user = str(interaction.user)
    if user not in user_config or "twitter_access_key" not in user_config[user]:
        await interaction.followup.send(
            f"No configuration or Twitter authorization found for {user}. Please use /set_config and /authorize_twitter to set it up."
        )
        return

    config = user_config[user]
    twitter_oauth = OAuth1Session(
        TWITTER_CONSUMER_KEY,
        client_secret=TWITTER_CONSUMER_SECRET,
        resource_owner_key=config["twitter_access_key"],
        resource_owner_secret=config["twitter_access_secret"],
    )

    # Ensure the correct path to the main.py script
    script_path = os.path.join(os.getcwd(), "main.py")
    command = ["python3", script_path, user, edition_url]
    if precta:
        command.append("--precta")
    if postcta:
        command.append("--postcta")
    if thread:
        command.append("--thread")

    try:
        print(f"Running command: {' '.join(command)}")  # Log the command being run
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),  # Ensure the working directory is correct
        )
        if result.returncode == 0:
            await interaction.followup.send(f"Successfully ran the script for {user}.")
            print(f"Script output: {result.stdout}")  # Log the script output
        else:
            await interaction.followup.send(
                f"Error running the script: {result.stderr}"
            )
            print(f"Script error: {result.stderr}")  # Log the script error
    except Exception as e:
        await interaction.followup.send(f"Error running the script: {str(e)}")
        print(f"Exception: {str(e)}")  # Log the exception


bot.run(DISCORD_BOT_TOKEN)
