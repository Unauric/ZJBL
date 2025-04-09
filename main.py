import discord
from discord.ext import commands, tasks
import asyncio
import requests
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

# Store last seen tx signature to avoid duplicates
last_seen_signature = None

def get_latest_buy():
    # Use Solscan API to fetch the latest buy transaction for your token
    url = f"https://api.solscan.io/v1/account/tokens/{TOKEN_ADDRESS}?type=buy&limit=1"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Solscan API error: {response.status_code}")
            return None
        
        data = response.json()
        txs = data.get("data", [])
        if not txs:
            return None
        
        return txs[0]  # latest buy tx
    except Exception as e:
        print(f"❌ Exception while fetching from Solscan: {e}")
        return None

@tasks.loop(seconds=30)
async def check_birdeye_transactions():
    global last_seen_signature

    print("📡 Checking Solscan for new buys...", flush=True)
    latest_tx = get_latest_buy()

    if not latest_tx:
        print("⚠️ No recent buy transactions found.")
        return

    sig = latest_tx["signature"]
    if sig == last_seen_signature:
        print("⏳ No new buys.")
        return

    last_seen_signature = sig

    buyer = latest_tx.get("owner", "Unknown")
    amount = latest_tx.get("inAmount", 0) / 1e9  # assuming lamports to SOL
    usd_value = latest_tx.get("usdValue", 0.0)
    tx_link = f"https://solscan.io/tx/{sig}"

    msg = (
        f"🚀 **New Buy on Solscan!**\n"
        f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
        f"💰 Amount: {amount:.4f} SOL (~${usd_value:.2f})\n"
        f"[🔗 View on Solscan]({tx_link})"
    )

    print(f"📢 Sending to Discord: {msg}")
    channel = await bot.fetch_channel(CHANNEL_ID)
    await channel.send(msg)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    check_birdeye_transactions.start()

bot.run(DISCORD_TOKEN)
