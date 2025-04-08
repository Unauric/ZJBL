import discord
from discord.ext import commands, tasks
import requests
import os
from dotenv import load_dotenv

print("🚀 Starting bot...", flush=True)

load_dotenv()  # Load .env variables

# ====== CONFIGURATION ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")  # Your token address for your coin

# ====== DISCORD SETUP ======
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Important for reading/sending messages

bot = commands.Bot(command_prefix="!", intents=intents)

# Polling Interval (in seconds) for transaction checking
POLLING_INTERVAL = 60  # Check every 60 seconds

# Solscan API Endpoint
SOLSCAN_API_URL = f"https://api.solscan.io/token/txs?tokenAddress={TOKEN_ADDRESS}"

# ====== POLLING FUNCTION ======
def get_transactions():
    try:
        response = requests.get(SOLSCAN_API_URL)
        response.raise_for_status()
        data = response.json()

        transactions = data.get("data", [])
        if not transactions:
            print("⚠️ No transactions found.")
            return

        # Process each transaction (if any)
        for tx in transactions:
            print(f"Processing transaction: {tx}")
            
            buyer = tx['fromUserAccount']
            amount = int(tx['amount']) / (10 ** tx['decimals'])  # Correct amount considering decimals
            tx_signature = tx['signature']
            
            # Build message for Discord
            tx_link = f"https://solscan.io/tx/{tx_signature}"
            msg = (
                f"🚀 {amount:.2f} $YOURCOIN bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                f"[View on Solscan]({tx_link})"
            )

            # Send the message to Discord
            send_message_to_discord(msg)
    except Exception as e:
        print(f"❌ Error fetching transactions: {e}")

# Send message to Discord
async def send_message_to_discord(msg):
    channel = await bot.fetch_channel(CHANNEL_ID)
    await channel.send(msg)
    print(f"✅ Sent message to channel {CHANNEL_ID}")

# Start polling every polling interval
@tasks.loop(seconds=POLLING_INTERVAL)
async def transaction_polling():
    print("⏳ Checking for new transactions...")
    await bot.loop.run_in_executor(None, get_transactions)

# ====== BOT EVENTS ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    # Start the transaction polling task
    transaction_polling.start()

# Run the bot
bot.run(DISCORD_TOKEN)
