import discord
from discord.ext import commands
from flask import Flask, request
import threading
import asyncio
import os
from dotenv import load_dotenv

print("🚀 Starting bot...", flush=True)

load_dotenv()

# ====== CONFIGURATION ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")

# ====== DISCORD SETUP ======
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Needed for reading/sending messages

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== FLASK SETUP ======
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    print("📬 Webhook received!", flush=True)

    try:
        data = request.get_json(force=True)
        print("📬 Webhook data:", data, flush=True)

        if 'transactions' not in data:
            print("⚠️ No transactions found in the webhook data.", flush=True)
            return {"status": "error", "message": "No transactions found"}, 400

        for tx in data.get("transactions", []):
            print(f"🔄 Processing transaction {tx}", flush=True)
            events = tx.get("events", {}).get("tokenTransfers", [])
            for event in events:
                print(f"🔍 Processing token transfer event {event}", flush=True)
                if event.get("tokenAddress") == TOKEN_ADDRESS:
                    print("✅ Found matching token address!", flush=True)
                    buyer = event.get("fromUserAccount", "unknown")
                    amount = int(event["amount"]) / (10 ** int(event.get("decimals", 0)))
                    tx_link = f"https://solscan.io/tx/{tx['signature']}"

                    msg = (
                        f"🚀 **{amount:.2f} $YOURCOIN** bought by `{buyer[:4]}...{buyer[-4:]}`\n"
                        f"[🔗 View on Solscan]({tx_link})"
                    )

                    async def send_message():
                        channel = await bot.fetch_channel(CHANNEL_ID)
                        await channel.send(msg)
                        print(f"✅ Sent message to channel {CHANNEL_ID}", flush=True)

                    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)

        return {"status": "ok"}, 200

    except Exception as e:
        print(f"❌ Error processing webhook: {e}", flush=True)
        return {"status": "error", "message": str(e)}, 500


# ====== BOT EVENTS ======
@bot.event

async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    check_pumpfun_transactions.start()


    for guild in bot.guilds:
        print(f"📌 Connected to guild: {guild.name} (ID: {guild.id})", flush=True)
        for channel in guild.text_channels:
            print(f"   └─ 💬 {channel.name} (ID: {channel.id})", flush=True)


import aiohttp
from discord.ext import tasks

last_seen_signature = None  # Tracks last transaction to avoid duplicates
PUMP_API_URL = f"https://pump.fun/api/trades/{TOKEN_ADDRESS}"

@tasks.loop(seconds=10)
async def check_pumpfun_transactions():
    global last_seen_signature
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PUMP_API_URL) as resp:
                if resp.status != 200:
                    print(f"❌ API error: {resp.status}")
                    return

                data = await resp.json()
                if not data:
                    print("⚠️ No data returned from Pump.fun")
                    return

                latest_tx = data[0]  # Most recent transaction
                sig = latest_tx.get("signature")

                if sig == last_seen_signature:
                    return  # No new transaction

                last_seen_signature = sig

                buyer = latest_tx.get("buyer", "Unknown")
                amount = latest_tx.get("amount", 0)
                price = latest_tx.get("price", 0)
                market_cap = latest_tx.get("marketCap", 0)
                tx_link = f"https://solscan.io/tx/{sig}"

                msg = (
                    f"🚀 **New Buy on Pump.fun!**\n"
                    f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
                    f"💸 Amount: {amount:.4f} SOL at {price:.4f} SOL/token\n"
                    f"📈 Market Cap: {market_cap} SOL\n"
                    f"[🔗 View on Solscan]({tx_link})"
                )

                channel = await bot.fetch_channel(CHANNEL_ID)
                await channel.send(msg)
                print(f"✅ Sent Pump.fun alert: {sig}")

    except Exception as e:
        print(f"❌ Error in check_pumpfun_transactions: {e}")


# ====== FLASK IN THREAD ======
def run_flask():
    app.run(host="0.0.0.0", port=5000)


# Start Flask in a separate thread
threading.Thread(target=run_flask).start()

# Run the Discord bot
bot.run(DISCORD_TOKEN)
