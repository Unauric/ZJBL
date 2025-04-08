import requests
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ====== CONFIGURATION ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = "Dj3wnBYJZGnzMkGGyUqLbtyU1bt4CaFF9mES44Nhpump"  # Replace with your coin's Solana token address

# ====== DISCORD SETUP ======
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Solana API URL
SOLANA_API_URL = "https://api.mainnet-beta.solana.com"

# Function to check for new transactions related to your token address
def check_solana_transactions():
    headers = {
        "Content-Type": "application/json"
    }

    # Request body for checking recent transactions involving the token address
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getConfirmedSignaturesForAddress2",
        "params": [TOKEN_ADDRESS, {"limit": 5}]  # Limit to 5 recent transactions
    }

    try:
        response = requests.post(SOLANA_API_URL, json=payload, headers=headers)
        transactions = response.json().get('result', [])
        if transactions:
            for tx in transactions:
                tx_signature = tx['signature']
                print(f"New transaction found: {tx_signature}")
                check_transaction_details(tx_signature)
    except Exception as e:
        print(f"Error checking Solana transactions: {e}")

# Function to get details about a specific transaction
def check_transaction_details(signature):
    headers = {
        "Content-Type": "application/json"
    }

    # Request body for checking transaction details
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature]
    }

    try:
        response = requests.post(SOLANA_API_URL, json=payload, headers=headers)
        transaction_details = response.json().get('result', {})

        if not transaction_details:
            print("No transaction details found.")
            return
        
        # Extracting transaction details
        transaction_meta = transaction_details.get('meta', {})
        token_balances = transaction_meta.get('postTokenBalances', [])

        for balance in token_balances:
            if balance.get('mint') == TOKEN_ADDRESS:
                amount = balance.get('uiAmount')  # Token amount
                buyer = transaction_details['transaction']['message']['accountKeys'][1]  # Account that made the transfer

                # Prepare the message
                msg = f"🚀 {amount} tokens bought by `{buyer[:4]}...{buyer[-4:]}`"

                # Send to Discord
                send_discord_message(msg)

    except Exception as e:
        print(f"Error getting transaction details: {e}")

# Function to send a message to Discord
async def send_discord_message(msg):
    channel = await bot.fetch_channel(CHANNEL_ID)
    await channel.send(msg)
    print(f"✅ Sent message to channel {CHANNEL_ID}")

# ====== BOT EVENTS ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)

# Poll the Solana blockchain every 60 seconds
def poll_solana():
    while True:
        check_solana_transactions()
        time.sleep(60)  # Sleep for 60 seconds before checking again

# Start polling Solana in a separate thread
import threading
threading.Thread(target=poll_solana).start()

# Run the bot
bot.run(DISCORD_TOKEN)
