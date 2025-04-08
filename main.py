import discord
from discord.ext import commands, tasks
import requests
import asyncio
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")
SOLSCAN_API_URL = "https://public-api.solscan.io/transaction"  # Solscan API endpoint (for example)

# Initialize Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Polling interval in seconds (e.g., 60 seconds)
POLLING_INTERVAL = 60

# ====== Polling Task to Check Transactions ======
@tasks.loop(seconds=POLLING_INTERVAL)
async def check_new_transactions():
    print("🔄 Checking for new transactions...")
    try:
        # Make an API request to Solscan (or Solana RPC) to fetch transactions
        response = requests.get(SOLSCAN_API_URL, params={"token": TOKEN_ADDRESS, "limit": 10})
        
        if response.status_code == 200:
            transactions = response.json().get("data", [])
            for tx in transactions:
                signature = tx.get("signature")
                token_transfers = tx.get("tokenTransfers", [])

                for transfer in token_transfers:
                    if transfer.get("tokenAddress") == TOKEN_ADDRESS:
                        # Process the token transfer event
                        buyer = transfer.get("fromUserAccount")
                        amount = int(transfer.get("amount")) / (10 ** transfer.get("decimals"))
                        tx_link = f"https://solscan.io/tx/{signature}"

                        msg = (
                            f"🚀 {amount:.2f} YOURCOIN bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                            f"[View on Solscan]({tx_link})"
                        )
                        # Send the message to the Discord channel
                        channel = await bot.fetch_channel(CHANNEL_ID)
                        await channel.send(msg)
                        print(f"✅ Sent message for transaction {signature}")
        else:
            print(f"❌ Failed to fetch transactions: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error while checking transactions: {e}")

# Start the polling task when the bot is ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    check_new_transactions.start()

# Run the bot
bot.run(DISCORD_TOKEN)
