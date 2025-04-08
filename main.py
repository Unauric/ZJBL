import discord
from discord.ext import commands
from flask import Flask, request
import threading
import asyncio
import os  # For accessing environment variables

from dotenv import load_dotenv
load_dotenv()  # Load variables from .env file

# ====== CONFIGURATION ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Must be cast to int
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")

app = Flask(__name__)

# ====== DISCORD INTENTS ======
# Enable all required intents, including privileged 'message_content'
intents = discord.Intents.default()
intents.message_content = True  # This is the privileged intent required
bot = commands.Bot(command_prefix="!", intents=intents)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)

    async def send_message():
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
                    try:
                        channel = await bot.fetch_channel(CHANNEL_ID)
                        if channel:
                            await channel.send(msg)
                            print(f"✅ Message sent to channel {CHANNEL_ID}")
                        else:
                            print(f"⚠️ Channel not found: {CHANNEL_ID}")
                    except Exception as e:
                        print(f"❌ Error sending message: {e}")

    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)
    return {"status": "ok"}, 200


def run_flask():
    app.run(host="0.0.0.0", port=5000)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        if channel:
            print(f"🔎 Found channel: {channel.name} (ID: {channel.id})")
        else:
            print(f"⚠️ Channel not found: {CHANNEL_ID}")
    except Exception as e:
        print(f"❌ Error fetching channel: {e}")


threading.Thread(target=run_flask).start()
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"❌ Error running bot: {e}")
