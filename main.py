import discord
from discord.ext import commands
from flask import Flask, request
import threading
import asyncio
import os
from dotenv import load_dotenv

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
    print("📬 Webhook received:", data)

    async def send_message():
        try:
            for tx in data.get("transactions", []):
                for event in tx.get("events", {}).get("tokenTransfers", []):
                    if event["tokenAddress"] == TOKEN_ADDRESS:
                        buyer = event["fromUserAccount"]
                        amount = int(event["amount"]) / (10 ** event["decimals"])
                        tx_link = f"https://solscan.io/tx/{tx['signature']}"
                        msg = (
                            f"🚀 {amount:.2f} $YOURCOIN bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                            f"[View on Solscan]({tx_link})"
                        )
                        channel = await bot.fetch_channel(CHANNEL_ID)
                        await channel.send(msg)
                        print(f"✅ Sent message to channel {CHANNEL_ID}")
        except Exception as e:
            print(f"❌ Error processing webhook: {e}")

    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)
    return {"status": "ok"}, 200


# ====== BOT EVENTS ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        print(f"🔎 Found channel: {channel.name}")
    except Exception as e:
        print(f"❌ Error fetching channel: {e}")


# ====== FLASK IN THREAD ======
def run_flask():
    app.run(host="0.0.0.0", port=5000)


threading.Thread(target=run_flask).start()
bot.run(DISCORD_TOKEN)
