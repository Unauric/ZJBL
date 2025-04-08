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
SOLSCAN_API_URL = os.getenv("SOLSCAN_API_URL")  # Now configurable from .env
POLLING_INTERVAL = 60  # Interval in seconds

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
        params = {"token": TOKEN_ADDRESS, "limit": 10}
        response = requests.get(SOLSCAN_API_URL, params=params, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP issues
        transactions = response.json().get("data", [])
        
        if transactions:
            print(f"Found {len(transactions)} transactions.")
            for tx in transactions:
                signature = tx.get("signature")
                if signature in processed_signatures:
                    continue  # Skip already processed transactions
                
                processed_signatures.add(signature)
                token_transfers = tx.get("tokenTransfers", [])
                for transfer in token_transfers:
                    if transfer.get("tokenAddress") == TOKEN_ADDRESS:
                        buyer = transfer.get("fromUserAccount")
                        amount = int(transfer.get("amount")) / (10 ** transfer.get("decimals"))
                        tx_link = f"https://solscan.io/tx/{signature}"
                        msg = (
                            f"🚀 {amount:.2f} YOURCOIN bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                            f"[View on Solscan]({tx_link})"
                        )
                        try:
                            channel = await bot.fetch_channel(CHANNEL_ID)
                            await channel.send(msg)
                            print(f"✅ Sent message for transaction {signature}")
                            await asyncio.sleep(1)  # Prevent rate limiting
                        except discord.HTTPException as e:
                            print(f"❌ Error sending message: {e}")
        else:
            print("🔄 No transactions found.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error while checking transactions: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}.")
    try:
        if not check_new_transactions.is_running():
            print("🔄 Starting transaction polling task.")
            check_new_transactions.start()
    except Exception as e:
        print(f"❌ Failed to start the polling task: {e}")

print("🛠️ Starting the bot...")
bot.run(DISCORD_TOKEN)
