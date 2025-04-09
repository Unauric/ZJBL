import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

print("🚀 Starting bot...", flush=True)

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Solscan API URL
SOLSCAN_API_URL = f"https://api.solscan.io/v1/transaction?address={TOKEN_ADDRESS}"

# Track last seen signature
last_seen_signature = None

# Solscan API polling setup
@tasks.loop(seconds=10)
async def check_solscan_transactions():
    global last_seen_signature
    try:
        print(f"📡 Fetching data from Solscan: {SOLSCAN_API_URL}", flush=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(SOLSCAN_API_URL) as resp:
                print(f"🌐 Solscan API status code: {resp.status}", flush=True)
                if resp.status != 200:
                    print(f"❌ Failed to fetch data from Solscan", flush=True)
                    return

                data = await resp.json()
                print(f"📊 Solscan API data: {data}", flush=True)

                if not data or not isinstance(data, list):
                    print("⚠️ No valid data returned from Solscan", flush=True)
                    return

                latest_tx = data[0]  # Most recent transaction
                sig = latest_tx.get("signature")

                if sig == last_seen_signature:
                    print("⏳ No new transaction since last check.", flush=True)
                    return  # No new transaction

                # New transaction detected
                last_seen_signature = sig

                buyer = latest_tx.get("buyer", "Unknown")
                amount = latest_tx.get("amount", 0)
                price = latest_tx.get("price", 0)
                market_cap = latest_tx.get("marketCap", 0)
                tx_link = f"https://solscan.io/tx/{sig}"

                msg = (
                    f"🚀 **New Buy on Solscan!**\n"
                    f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
                    f"💸 Amount: {amount:.4f} SOL at {price:.4f} SOL/token\n"
                    f"📈 Market Cap: {market_cap} SOL\n"
                    f"[🔗 View on Solscan]({tx_link})"
                )

                print(f"📢 Sending message to Discord: {msg}", flush=True)

                # Send message to Discord channel
                channel = await bot.fetch_channel(CHANNEL_ID)
                await channel.send(msg)
                print(f"✅ Sent Solscan alert for tx {sig}", flush=True)

    except Exception as e:
        print(f"❌ Error in check_solscan_transactions: {e}", flush=True)

# Bot event to start the transaction check loop
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    check_solscan_transactions.start()
    for guild in bot.guilds:
        print(f"📌 Connected to guild: {guild.name} (ID: {guild.id})", flush=True)
        for channel in guild.text_channels:
            print(f"   └─ 💬 {channel.name} (ID: {channel.id})", flush=True)

bot.run(DISCORD_TOKEN)
