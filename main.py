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

# Moralis API setup
API_URL = f"https://solana-gateway.moralis.io/token/mainnet/{TOKEN_ADDRESS}/swaps?order=DESC"
API_HEADERS = {
    "Accept": "application/json",
    "X-API-Key": os.getenv("MORALIS_API_KEY")  # Ensure to set this in your .env file
}

# Store the last seen transaction hash to prevent duplicate alerts
last_seen_signature = None

def get_transactions():
    """Fetches the latest transactions using the Moralis API."""
    try:
        response = requests.get(API_URL, headers=API_HEADERS)
        if response.status_code != 200:
            print(f"❌ Failed to fetch data from Moralis API. Status code: {response.status_code}")
            return []

        data = response.json()
        if not data.get('result'):
            print("⚠️ No transactions found.")
            return []

        transactions = []
        for tx in data['result']:
            signature = tx.get("transactionHash", "N/A")
            buyer = tx.get("bought", {}).get("name", "Unknown")
            amount = tx.get("bought", {}).get("value", "0")
            price = tx.get("price", "0")

            transactions.append({
                'signature': signature,
                'buyer': buyer,
                'amount': amount,
                'price': price
            })

        return transactions
    except Exception as e:
        print(f"❌ Error fetching or parsing Moralis API data: {e}")
        return []

@tasks.loop(seconds=60)  # Check every 60 seconds
async def check_moralis_transactions():
    global last_seen_signature

    try:
        print(f"📡 Fetching data from Moralis API: {API_URL}", flush=True)
        transactions = get_transactions()

        if not transactions:
            print("⚠️ No transactions found or failed to fetch data.", flush=True)
            return

        latest_tx = transactions[0]  # Most recent transaction
        sig = latest_tx['signature']

        if sig == last_seen_signature:
            print("⏳ No new transaction since last check.", flush=True)
            return  # No new transaction

        # New transaction detected
        last_seen_signature = sig

        buyer = latest_tx.get("buyer", "Unknown")
        amount = latest_tx.get("amount", "0")
        price = latest_tx.get("price", "0")
        tx_link = f"https://solscan.io/tx/{sig}"  # Moralis doesn't provide a link, so fallback to Solscan

        msg = (
            f"🚀 **New Buy on Solana Token!**\n"
            f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
            f"💸 Amount: {amount} SOL at {price} SOL/token\n"
            f"[🔗 View on Solscan]({tx_link})"
        )

        print(f"📢 Sending message to Discord: {msg}", flush=True)

        channel = await bot.fetch_channel(CHANNEL_ID)
        await channel.send(msg)
        print(f"✅ Sent Moralis alert for tx {sig}", flush=True)

    except Exception as e:
        print(f"❌ Error in check_moralis_transactions: {e}", flush=True)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    check_moralis_transactions.start()
    for guild in bot.guilds:
        print(f"📌 Connected to guild: {guild.name} (ID: {guild.id})", flush=True)
        for channel in guild.text_channels:
            print(f"   └─ 💬 {channel.name} (ID: {channel.id})", flush=True)

bot.run(DISCORD_TOKEN)
