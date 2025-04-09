import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import asyncio

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

# Solscan URL for your token
solscan_url = f"https://solscan.io/token/{TOKEN_ADDRESS}"

# Track last seen transaction signature to avoid sending duplicate messages
last_seen_signature = None

# Scrape transaction data from Solscan
def scrape_solscan():
    global last_seen_signature
    try:
        # Send GET request to Solscan token page
        response = requests.get(solscan_url)
        
        # If the request is successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find all transaction rows (update the class selector as per actual Solscan structure)
            transactions = soup.find_all("div", class_="transaction-row")  # Example, adjust as needed
            
            for tx in transactions:
                tx_hash = tx.find("a", class_="txHash").get("href")
                buyer = tx.find("div", class_="buyer").get_text()
                amount = tx.find("div", class_="amount").get_text()
                signature = tx_hash.split('/')[-1]  # Assuming the tx hash is part of the URL
                
                # If this is a new transaction
                if signature != last_seen_signature:
                    # Update the last seen signature
                    last_seen_signature = signature

                    # Construct the message to send to Discord
                    msg = (
                        f"🚀 **New Buy on Solscan!**\n"
                        f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
                        f"💸 Amount: {amount}\n"
                        f"[🔗 View Transaction]({tx_hash})"
                    )

                    # Send the message to Discord
                    asyncio.run(send_message(msg))

        else:
            print(f"❌ Failed to retrieve the Solscan page. Status code: {response.status_code}")

    except Exception as e:
        print(f"❌ Error in scraping Solscan: {e}")


# Send the message to the Discord channel
async def send_message(msg):
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        await channel.send(msg)
        print(f"✅ Sent transaction alert: {msg}")
    except Exception as e:
        print(f"❌ Error sending message to Discord: {e}")


# Periodically check for new transactions every 60 seconds
@tasks.loop(seconds=60)
async def check_transactions():
    print("📡 Checking for new transactions...")
    scrape_solscan()


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    check_transactions.start()


bot.run(DISCORD_TOKEN)
