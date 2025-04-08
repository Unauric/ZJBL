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
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})", flush=True)

    guild = discord.utils.get(client.guilds, name=GUILD_NAME)
    if guild:
        print(f"🔎 Found guild: {guild.name} (ID: {guild.id})", flush=True)
        channel = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
        if channel:
            print(f"💬 Found channel: {channel.name} (ID: {channel.id})", flush=True)
        else:
            print(f"⚠️ Channel '{CHANNEL_NAME}' not found in guild '{GUILD_NAME}'", flush=True)
    else:
        print(f"⚠️ Guild '{GUILD_NAME}' not found", flush=True)



# ====== FLASK IN THREAD ======
def run_flask():
    app.run(host="0.0.0.0", port=5000)


threading.Thread(target=run_flask).start()
bot.run(DISCORD_TOKEN)
