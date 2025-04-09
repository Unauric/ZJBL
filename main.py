import discord
from discord.ext import commands, tasks
import asyncio
import requests
from bs4 import BeautifulSoup
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

# Solscan scraping setup
last_seen_signature = None
SOLSCAN_URL = f"https://solscan.io/token/{TOKEN_ADDRESS}"

def get_transactions():
    """Scrapes the Solscan page for transactions and returns the latest transaction data."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(SOLSCAN_URL, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to fetch data from Solscan. Status code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find transaction data in the page
        transactions = []
        rows = soup.find_all('tr', class_='table-row')  # Find rows with transaction data
        for row in rows:
            signature = row.find('td', class_='text-left').text.strip()
            buyer = row.find_all('td', class_='text-center')[1].text.strip()  # Adjust this index based on the actual layout
            amount = row.find_all('td', class_='text-right')[1].text.strip()  # Adjust this index based on the actual layout
            price = row.find_all('td', class_='text-right')[2].text.strip()  # Adjust this index based on the actual layout

            transactions.append({
                'signature': signature,
                'buyer': buyer,
                'amount': amount,
                'price': price
            })
        
        return transactions
    except Exception as e:
        print(f"❌ Error fetching or parsing Solscan data: {e}")
        return []


@tasks.loop(seconds=60)  # Check every 60 seconds
async def check_solscan_transactions():
    global last_seen_signature

    try:
        print(f"📡 Fetching data from Solscan: {SOLSCAN_URL}", flush=True)
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
        tx_link = f"https://solscan.io/tx/{sig}"

        msg = (
            f"🚀 **New Buy on Solscan!**\n"
            f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
            f"💸 Amount: {amount} SOL at {price} SOL/token\n"
            f"[🔗 View on Solscan]({tx_link})"
        )

        print(f"📢 Sending message to Discord: {msg}", flush=True)

        channel = await bot.fetch_channel(CHANNEL_ID)
        await channel.send(msg)
        print(f"✅ Sent Solscan alert for tx {sig}", flush=True)

    except Exception as e:
        print(f"❌ Error in check_solscan_transactions: {e}", flush=True)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    check_solscan_transactions.start()
    for guild in bot.guilds:
        print(f"📌 Connected to guild: {guild.name} (ID: {guild.id})", flush=True)
        for channel in guild.text_channels:
            print(f"   └─ 💬 {channel.name} (ID: {channel.id})", flush=True)

bot.run(DISCORD_TOKEN)
