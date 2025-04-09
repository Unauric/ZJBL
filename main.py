import discord
from discord.ext import tasks, commands
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load env variables (optional, or replace with direct strings)
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Or paste your token here
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))   # Or paste your channel ID here

# Pump.fun target
TOKEN_ADDRESS = "Dj3wnBYJZGnzMkGGyUqLbtyU1bt4CaFF9mES44Nhpump"
PUMP_API_URL = f"https://pump.fun/api/trades/{TOKEN_ADDRESS}"

# Discord bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

last_seen_signature = None  # to avoid duplicates

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_pumpfun_transactions.start()

@tasks.loop(seconds=10)  # checks every 10 seconds
async def check_pumpfun_transactions():
    global last_seen_signature
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PUMP_API_URL) as resp:
                if resp.status != 200:
                    print(f"❌ API error: {resp.status}")
                    return

                data = await resp.json()

                if not data or len(data) == 0:
                    print("⚠️ No recent trades.")
                    return

                latest_tx = data[0]  # Most recent transaction
                sig = latest_tx.get("signature")

                if sig == last_seen_signature:
                    return  # already processed

                last_seen_signature = sig  # update seen sig

                buyer = latest_tx.get("buyer", "Unknown")
                amount = latest_tx.get("amount", 0)
                price = latest_tx.get("price", 0)
                market_cap = latest_tx.get("marketCap", 0)
                tx_link = f"https://solscan.io/tx/{sig}"

                message = (
                    f"🚀 **New Buy on Pump.fun!**\n"
                    f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
                    f"💸 Amount: {amount:.4f} SOL at {price:.4f} SOL/token\n"
                    f"📈 New Market Cap: {market_cap} SOL\n"
                    f"[🔗 View on Solscan]({tx_link})"
                )

                channel = bot.get_channel(CHANNEL_ID)
                if channel:
                    await channel.send(message)
                    print(f"✅ Alert sent: {sig}")

    except Exception as e:
        print(f"❌ Error fetching Pump.fun data: {e}")

print("🛠️ Starting bot...")
bot.run(DISCORD_TOKEN)
