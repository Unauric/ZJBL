import discord
from discord.ext import commands
from flask import Flask, request
import threading
import asyncio
import os
from dotenv import load_dotenv

# ====== INITIAL SETUP ======
print("🚀 Starting bot...", flush=True)
load_dotenv()  # Load environment variables

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Bot token from the .env file
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Target channel ID
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")  # Your token address for purchases

# ====== DISCORD BOT CONFIGURATION ======
intents = discord.Intents.default()
intents.message_content = True  # Required to send and fetch messages
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== FLASK SETUP ======
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming webhook events from Pump.fun."""
    print("📬 Webhook received!")  # Debugging webhook trigger

    try:
        # Parse incoming JSON data
        data = request.get_json(force=True)
        print("📬 Webhook Data:", data)  # Debug incoming webhook payload
        
        # Verify 'transactions' exist in the webhook payload
        if 'transactions' not in data:
            print("⚠️ No 'transactions' found in webhook data.")
            return {"status": "error", "message": "No transactions found"}, 400

        # Process each transaction
        for tx in data.get("transactions", []):
            for event in tx.get("events", {}).get("tokenTransfers", []):
                if event.get("tokenAddress") == TOKEN_ADDRESS:  # Match token address
                    print("✅ Valid transaction detected!")  # Debug matching transaction

                    # Extract purchase details
                    buyer = event["fromUserAccount"]
                    amount = int(event["amount"]) / (10 ** event["decimals"])
                    tx_link = f"https://solscan.io/tx/{tx['signature']}"
                    
                    # Format message
                    message = (
                        f"🚀 {amount:.2f} $YOURCOIN bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                        f"[View on Solscan]({tx_link})"
                    )
                    
                    # Define async function to send message
                    async def send_message():
                        try:
                            channel = await bot.fetch_channel(CHANNEL_ID)
                            if channel:
                                await channel.send(message)
                                print(f"✅ Message sent to channel {CHANNEL_ID}")
                            else:
                                print(f"⚠️ Could not find channel with ID {CHANNEL_ID}")
                        except Exception as e:
                            print(f"❌ Error sending message: {e}")

                    # Execute send_message coroutine in the bot's loop
                    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)

        return {"status": "ok"}, 200
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}, 500

# ====== DISCORD BOT EVENTS ======
@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        if channel:
            print(f"💬 Ready to send messages to channel: {channel.name} (ID: {channel.id})")
        else:
            print("⚠️ Channel not found or invalid ID")
    except Exception as e:
        print(f"❌ Error fetching channel: {e}", flush=True)

# ====== FLASK IN SEPARATE THREAD ======
def run_flask():
    """Runs the Flask server in a separate thread."""
    print("🌐 Starting Flask server...", flush=True)
    app.run(host="0.0.0.0", port=5000)

# Start the Flask server
threading.Thread(target=run_flask).start()

# Run the Discord bot
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"❌ Error starting bot: {e}", flush=True)
