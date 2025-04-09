import discord
from discord.ext import commands, tasks
import requests
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")
PUMPFUN_API_URL = "https://api.pump.fun/v1/transactions"
POLLING_INTERVAL = 60  # Polling interval in seconds

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Track processed transaction signatures
processed_signatures = set()

@tasks.loop(seconds=POLLING_INTERVAL)
async def check_new_transactions():
    print("🔄 Checking for new transactions...")
    try:
        params = {"tokenAddress": TOKEN_ADDRESS, "limit": 10}
        response = requests.get(PUMPFUN_API_URL, params=params, timeout=10)
        response.raise_for_status()
        transactions = response.json().get("transactions", [])

        if transactions:
            print(f"📡 Found {len(transactions)} transactions.")
            for tx in transactions:
                signature = tx.get("signature")
                if signature in processed_signatures:
                    continue

                processed_signatures.add(signature)
                buyer = tx.get("buyer")
                amount = tx.get("amount")
                market_cap = tx.get("marketCap")
                buyer_name = tx.get("buyerName", "Unknown")
                tx_link = f"https://solscan.io/tx/{signature}"
                msg = (
                    f"🚀 {amount} tokens purchased by {buyer_name} (`{buyer}`)\n"
                    f"💰 New Market Cap: {market_cap}\n"
                    f"[View Transaction]({tx_link})"
                )
                try:
                    channel = await bot.fetch_channel(CHANNEL_ID)
                    await channel.send(msg)
                    print(f"✅ Sent message for transaction {signature}")
                    await asyncio.sleep(1)
                except discord.HTTPException as e:
                    print(f"❌ Error sending message: {e}")
        else:
            print("🔄 No new transactions found.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error while checking transactions: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user} (ID: {bot.user.id})")
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        if channel:
            print(f"🔎 Found channel: {channel.name} (ID: {channel.id})")
        else:
            print(f"⚠️ Channel not found with ID {CHANNEL_ID}")

        if not check_new_transactions.is_running():
            print("🔄 Starting transaction polling task.")
            check_new_transactions.start()
    except Exception as e:
        print(f"❌ Error in on_ready(): {e}")

print("🛠️ Starting the bot...")
bot.run(DISCORD_TOKEN)
