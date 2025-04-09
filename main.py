import discord
from discord.ext import tasks, commands
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load .env variables or use fallback defaults
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Replace with your real channel ID

# Pump.fun target
TOKEN_ADDRESS = "Dj3wnBYJZGnzMkGGyUqLbtyU1bt4CaFF9mES44Nhpump"
PUMP_API_URL = f"https://pump.fun/api/trades/{TOKEN_ADDRESS}"

# Setup Discord bot with proper intents
intents = discord.Intents.default()
intents.guilds = True  # Needed for on_ready to work
bot = commands.Bot(command_prefix="!", intents=intents)

last_seen_signature = None  # To avoid duplicate processing


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("🔁 Starting transaction check loop...")
    check_pumpfun_transactions.start()


@tasks.loop(seconds=10)  # Runs every 10 seconds
async def check_pumpfun_transactions():
    global last_seen_signature

    print("📡 Checking Pump.fun for latest trades...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PUMP_API_URL) as resp:
                if resp.status != 200:
                    print(f"❌ API error: Status code {resp.status}")
                    return

                data = await resp.json()
                if not data:
                    print("⚠️ No recent trades found.")
                    return

                latest_tx = data[0]
                sig = latest_tx.get("signature")

                if sig == last_seen_signature:
                    print("⏩ Already processed latest transaction.")
                    return

                last_seen_signature = sig  # Mark as processed

                # Parse data
                buyer = latest_tx.get("buyer", "Unknown")
                amount = latest_tx.get("amount", 0)
                price = latest_tx.get("price", 0)
                market_cap = latest_tx.get("marketCap", 0)
                tx_link = f"https://solscan.io/tx/{sig}"

                message = (
                    f"🚀 **New Buy on Pump.fun!**\n"
                    f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
                    f"💸 Amount: {amount:.4f} SOL at {price:.4f} SOL/token\n"
                    f"📈 New Market Cap: {market_cap} SOL\n"
                    f"[🔗 View on Solscan]({tx_link})"
                )

                # Send message to the channel
                channel = bot.get_channel(CHANNEL_ID)
                if channel is None:
                    print(f"❌ Error: Channel with ID {CHANNEL_ID} not found or bot has no access.")
                    return

                try:
                    await channel.send(message)
                    print(f"✅ Alert sent for transaction: {sig}")
                except Exception as e:
                    print(f"❌ Failed to send message: {e}")

    except Exception as e:
        print(f"❌ Error fetching Pump.fun data: {e}")


# Start the bot
print("🛠️ Starting bot...")
if not DISCORD_TOKEN or CHANNEL_ID == 123456789012345678:
    print("❌ ERROR: Please set your DISCORD_TOKEN and CHANNEL_ID in the .env file or directly in the script.")
else:
    bot.run(DISCORD_TOKEN)
