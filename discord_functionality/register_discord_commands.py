from dotenv import load_dotenv
import requests
import os

load_dotenv()


def register_command():
    application_id = os.getenv("DISCORD_APP_ID")
    guild_id = os.getenv("GUILD_ID")
    bot_token = os.getenv("DISCORD_BOT_TOKEN")

    url = f"https://discord.com/api/v10/applications/{application_id}/guilds/{guild_id}/commands"

    json = {
        "name": "enter_pin",
        "type": 1,  # Slash command
        "description": "Enter the Twitter authorization PIN",
        "options": [
            {
                "name": "pin_code",
                "description": "PIN code from Twitter authorization",
                "type": 3,  # STRING type
                "required": True,
            }
        ],
    }

    headers = {"Authorization": f"Bot {bot_token}"}

    response = requests.post(url, headers=headers, json=json)
    if response.status_code == 201:
        print("Command registered successfully")
    else:
        print(f"Failed to register command: {response.status_code}, {response.text}")


register_command()
