import discord
from discord.ext import commands
from flask import Flask, request
import threading
import asyncio
import os
from dotenv import load_dotenv

print("🚀 Starting bot...", flush=True)

load_dotenv()  # Load .env variables

# ====== CONFIGURATION ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")

# ====== DISCORD SETUP ======
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Important for reading/sending messages

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== FLASK SETUP ======
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    print("📬 Webhook received!")  # Confirm receipt of webhook

    try:
        # Debugging: print raw request data
        print(f"📬 Raw Request Data: {request.data}")

        # Read incoming data
        data = request.get_json(force=True)
        print("📬 Webhook data:", data)  # Print out the incoming data for debugging
        
        # Check if 'transactions' are present in the data
        if 'transactions' not in data:
            print("⚠️ No transactions found in the webhook data.")
            return {"status": "error", "message": "No transactions found"}, 400

        # Process the transactions
        for tx in data.get("transactions", []):
            print(f"Processing transaction: {tx}")  # Debug: print each transaction
            for event in tx.get("events", {}).get("tokenTransfers", []):
                print(f"Processing token transfer event: {event}")  # Debug: print each token transfer event
                if event.get("tokenAddress") == TOKEN_ADDRESS:
                    print("✅ Found matching token address!")  # Token address matched
                    buyer = event["fromUserAccount"]
                    amount = int(event["amount"]) / (10 ** event["decimals"])
                    tx_link = f"https://solscan.io/tx/{tx['signature']}"
                    msg = (
                        f"🚀 {amount:.2f} $YOURCOIN bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                        f"[View on Solscan]({tx_link})"
                    )

                    # Ensure we're using an async method correctly to send the message
                    async def send_message():
                        try:
                            channel = await bot.fetch_channel(CHANNEL_ID)
                            if channel:
                                await channel.send(msg)
                                print(f"✅ Sent message to channel {CHANNEL_ID}")
                            else:
                                print(f"⚠️ Could not find channel with ID {CHANNEL_ID}")
                        except Exception as e:
                            print(f"❌ Error sending message: {e}")
                    
                    # Run the coroutine safely within the bot's loop
                    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)

        return {"status": "ok"}, 200
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}, 500

# ====== BOT EVENTS ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)

    try:
        guild = discord.utils.get(bot.guilds, name="$MAYBACH420")  # Replace with actual guild name
        if guild:
            print(f"🔎 Found guild: {guild.name} (ID: {guild.id})", flush=True)
            channel = discord.utils.get(guild.text_channels, name="new-buy")  # Replace with actual channel name
            if channel:
                print(f"💬 Found channel: {channel.name} (ID: {channel.id})", flush=True)
            else:
                print(f"⚠️ Channel not found", flush=True)
        else:
            print(f"⚠️ Guild not found", flush=True)
    except Exception as e:
        print(f"❌ Error in on_ready event: {e}", flush=True)

# ====== FLASK IN THREAD ======
def run_flask():
    print("🌐 Starting Flask server...", flush=True)
    app.run(host="0.0.0.0", port=5000)

# Start Flask in a separate thread to handle incoming webhooks
threading.Thread(target=run_flask).start()

# Run the bot
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"❌ Error running bot: {e}", flush=True)
