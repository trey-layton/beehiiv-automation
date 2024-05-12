import os
import discord
from discord.ext import commands
from discord import app_commands, Intents, Client, Message
from dotenv import load_dotenv
from main import main
from random import choice, randint

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 795075911355596850  # Replace with your guild ID

intents: Intents = Intents.default()
intents.message_content = True

client: Client = Client(intents=intents)
bot = commands.Bot(command_prefix="/", intents=intents)


@bot.command(name="promote")
async def promote(ctx):
    await main.main()
    await ctx.send("Content generated successfully!")


bot.run(TOKEN)


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")


def main() -> None:
    client.run(token=TOKEN)


if __name__ == "__main__":
    main()
