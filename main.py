import discord
from discord.ext import commands
import requests
import threading
import asyncio
import os
from dotenv import load_dotenv
from flask import Flask, request

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
                        channel = await bot.fetch_channel(CHANNEL_ID)
                        await channel.send(msg)
                        print(f"✅ Sent message to channel {CHANNEL_ID}")
                    
                    # Ensure we're running this in the correct loop
                    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)

        return {"status": "ok"}, 200
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}, 500

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

# ====== FETCH TRANSACTION DATA FROM SOLSCAN ======
import requests

def fetch_and_send_transactions():
    # Define your Solscan token address and endpoint
    SOLSCAN_API_URL = f"https://api.solscan.io/account/txs?account={TOKEN_ADDRESS}&limit=10"

    try:
        # Fetch transaction data from Solscan
        response = requests.get(SOLSCAN_API_URL)
        
        # Log the status code and the raw response content for debugging
        print(f"Solscan API Response Status Code: {response.status_code}")
        print(f"Solscan API Response Content: {response.text}")
        
        # If the request was successful, try to parse the JSON response
        if response.status_code == 200:
            transactions = response.json().get("data", [])
        else:
            print(f"❌ Error: Solscan API returned an error with status code {response.status_code}")
            return
        
        # Sample structure to hold formatted data
        formatted_transactions = []

        for tx in transactions:
            # Checking if it's a token transfer transaction
            for event in tx.get("events", {}).get("tokenTransfers", []):
                if event.get("tokenAddress") == TOKEN_ADDRESS:
                    formatted_tx = {
                        "signature": tx["signature"],
                        "events": {
                            "tokenTransfers": [
                                {
                                    "tokenAddress": event["tokenAddress"],
                                    "fromUserAccount": event["fromUserAccount"],
                                    "amount": event["amount"],
                                    "decimals": event["decimals"]
                                }
                            ]
                        }
                    }
                    formatted_transactions.append(formatted_tx)

        # Now send the formatted transactions to the webhook
        if formatted_transactions:
            WEBHOOK_URL = "https://zjbl.onrender.com/webhook"
            response = requests.post(WEBHOOK_URL, json={"transactions": formatted_transactions})

            # Print the response for debugging
            print(f"Webhook Response Status Code: {response.status_code}")
            print(f"Webhook Response Text: {response.text}")
        else:
            print("⚠️ No matching transactions found to send to webhook.")

    except Exception as e:
        print(f"❌ Error occurred while fetching or sending transactions: {e}")


    # Print the response for debugging
    print(response.status_code, response.text)

# Run the fetch and send transaction function (you can call this every X minutes or trigger it based on events)
fetch_and_send_transactions()

# Run the bot
bot.run(DISCORD_TOKEN)
