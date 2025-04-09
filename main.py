import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("✅ on_ready() was called!")
    print(f"Logged in as: {bot.user} (ID: {bot.user.id})")

print("🚀 Starting bot...")
bot.run(DISCORD_TOKEN)
