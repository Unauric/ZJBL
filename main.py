import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

print("🚀 Starting bot...", flush=True)

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Pump.fun API polling setup
last_seen_signature = None
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

                latest_tx = data[0]
                sig = latest_tx.get("signature")

                if sig == last_seen_signature:
                    return

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

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    check_pumpfun_transactions.start()
    for guild in bot.guilds:
        print(f"📌 Connected to guild: {guild.name} (ID: {guild.id})", flush=True)
        for channel in guild.text_channels:
            print(f"   └─ 💬 {channel.name} (ID: {channel.id})", flush=True)

bot.run(DISCORD_TOKEN)
