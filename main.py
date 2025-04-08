import discord
from discord.ext import commands, tasks
import requests
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")
SOLSCAN_API_URL = "https://public-api.solscan.io/transaction"  # Solscan API endpoint

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
    print("🔄 Checking for new transactions...")  # Log to verify the task is being executed
    try:
        # Make an API request to Solscan (or Solana RPC) to fetch transactions
        params = {"token": TOKEN_ADDRESS, "limit": 10}
        response = requests.get(SOLSCAN_API_URL, params=params)

        # Check if the response status code is 200 (successful)
        if response.status_code == 200:
            print("📡 Successfully fetched transactions.")
            transactions = response.json().get("data", [])
            
            if transactions:
                print(f"Found {len(transactions)} transactions.")  # Log the number of transactions found
                for tx in transactions:
                    signature = tx.get("signature")
                    token_transfers = tx.get("tokenTransfers", [])

                    # Log the token transfers for this transaction
                    print(f"Processing transaction {signature} with {len(token_transfers)} token transfers.")

                    for transfer in token_transfers:
                        if transfer.get("tokenAddress") == TOKEN_ADDRESS:
                            # Process the token transfer event
                            buyer = transfer.get("fromUserAccount")
                            amount = int(transfer.get("amount")) / (10 ** transfer.get("decimals"))
                            tx_link = f"https://solscan.io/tx/{signature}"

                            # Construct the message
                            msg = (
                                f"🚀 {amount:.2f} YOURCOIN bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                                f"[View on Solscan]({tx_link})"
                            )

                            # Send the message to the Discord channel
                            channel = await bot.fetch_channel(CHANNEL_ID)
                            await channel.send(msg)
                            print(f"✅ Sent message for transaction {signature}")
            else:
                print("🔄 No transactions found.")
        else:
            print(f"❌ Failed to fetch transactions. Status Code: {response.status_code}")
            print("Response Content:", response.text)  # Log the response content for debugging
    except Exception as e:
        print(f"❌ Error while checking transactions: {e}")

# Start the polling task when the bot is ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    check_new_transactions.start()  # Ensure the polling task starts when the bot is ready

# Run the bot
bot.run(DISCORD_TOKEN)
