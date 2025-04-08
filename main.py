import discord
from discord.ext import commands
from flask import Flask, request
import threading
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")

app = Flask(__name__)

intents = discord.Intents.default()
intents.message_content = True  # ✅ Required for message access
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
                        await channel.send(msg)
                    except Exception as e:
                        print(f"❌ Failed to send message: {e}")

    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)
    return {"status": "ok"}, 200


def run_flask():
    app.run(host="0.0.0.0", port=5000)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        print("🔎 Found channel:", channel)
    except Exception as e:
        print(f"⚠️ Couldn't fetch channel: {e}")

threading.Thread(target=run_flask).start()
bot.run(DISCORD_TOKEN)
