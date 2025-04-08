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
    data = request.get_json(force=True)
    print("📬 Webhook received:", data)  # Print all received data

    async def send_message():
        try:
            for tx in data.get("transactions", []):
                print(f"Processing transaction: {tx}")  # Debug: print transaction
                for event in tx.get("events", {}).get("tokenTransfers", []):
                    print(f"Processing token transfer event: {event}")  # Debug: print token transfer
                    if event.get("tokenAddress") == TOKEN_ADDRESS:
                        buyer = event["fromUserAccount"]
                        amount = int(event["amount"]) / (10 ** event["decimals"])
                        tx_link = f"https://solscan.io/tx/{tx['signature']}"
                        msg = (
                            f"🚀 {amount:.2f} $YOURCOIN bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                            f"[View on Solscan]({tx_link})"
                        )

                        # Debug: Print to check if the correct channel is fetched
                        try:
                            channel = await bot.fetch_channel(CHANNEL_ID)
                            print(f"Fetched channel: {channel.name} (ID: {channel.id})")  # Debug: Check the fetched channel
                            if not channel.permissions_for(bot.user).send_messages:
                                print("❌ Bot does not have permission to send messages in this channel.")
                            else:
                                await channel.send(msg)
                                print(f"✅ Sent message to channel {CHANNEL_ID}")
                        except Exception as e:
                            print(f"❌ Error fetching channel: {e}")

        except Exception as e:
            print(f"❌ Error processing webhook: {e}")

    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)
    return {"status": "ok"}, 200


# ====== BOT EVENTS ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)

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


# ====== FLASK IN THREAD ======
def run_flask():
    app.run(host="0.0.0.0", port=5000)


# Start Flask in a separate thread to handle incoming webhooks
threading.Thread(target=run_flask).start()

# Run the bot
bot.run(DISCORD_TOKEN)
