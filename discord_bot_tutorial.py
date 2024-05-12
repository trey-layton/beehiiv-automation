import os
import discord
from discord.ext import commands
from discord import Intents, Client, Message
from dotenv import load_dotenv
from random import choice, randint

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 795075911355596850  # Replace with your guild ID

intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)


def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()
    if lowered == "test":
        return choice(["test a", "test b"])


async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print("(Message was empty because intents were not enabled probably)")
        return
    if is_private := user_message[0] == "?":
        user_message = user_message[1:]

    try:
        response: str = get_response(user_message)
        (
            await message.author.send(response)
            if is_private
            else await message.channel.send(response)
        )
    except Exception as e:
        print(e)


@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await send_message(message, user_message)


def main() -> None:
    client.run(token=TOKEN)


if __name__ == "__main__":
    main()
