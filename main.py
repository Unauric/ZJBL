import discord
from discord.ext import commands, tasks
import asyncio
import requests
import os
from dotenv import load_dotenv
import time
from discord.ext import tasks

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

# Moralis API setup
API_URL = f"https://solana-gateway.moralis.io/token/mainnet/{TOKEN_ADDRESS}/swaps?order=DESC"
API_HEADERS = {
    "Accept": "application/json",
    "X-API-Key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjExYjQ4YjQ4LWJhYjgtNDJkOC1iNzEyLTVhZWYwZWY0NGU1NiIsIm9yZ0lkIjoiNDQwODEwIiwidXNlcklkIjoiNDUzNTExIiwidHlwZUlkIjoiZTRmNzJlNWEtNmU5MS00NjRmLTg2NDktMDhiMzg5NzI0MTBhIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDQyMjQ3NzYsImV4cCI6NDg5OTk4NDc3Nn0.--O9_2uuC7l5xyg7CJ8Jktr0fuGbWfH8olLfbeKkqmI"
}

# Store the last seen transaction hash
last_seen_signature = None

def get_transactions():
    """Fetches the latest transactions using the Moralis API."""
    try:
        response = requests.get(API_URL, headers=API_HEADERS)
        if response.status_code != 200:
            print(f"❌ Failed to fetch data from Moralis API. Status code: {response.status_code}")
            return []

        data = response.json()
        if not data.get('result'):
            print("⚠️ No transactions found.")
            return []

        transactions = []
        for tx in data['result']:
            if tx.get("transactionType") == "buy":
                signature = tx.get("transactionHash", "N/A")
                wallet_address = tx.get("walletAddress", "Unknown")
                token_name = tx.get("bought", {}).get("name", "Unknown")
                usd_amount = tx.get("bought", {}).get("usdAmount", "0")

                transactions.append({
                    'signature': signature,
                    'wallet_address': wallet_address,
                    'token_name': token_name,
                    'usd_amount': usd_amount
                })

        return transactions
    except Exception as e:
        print(f"❌ Error fetching or parsing Moralis API data: {e}")
        return []

@tasks.loop(seconds=120)
async def check_moralis_transactions():
    global last_seen_signature

    try:
        print(f"📡 Fetching data from Moralis API: {API_URL}", flush=True)
        transactions = get_transactions()

        if not transactions:
            print("⚠️ No buy transactions found or failed to fetch data.", flush=True)
            return

        latest_tx = transactions[0]
        sig = latest_tx['signature']

        if sig == last_seen_signature:
            print("⏳ No new buy transaction since last check.", flush=True)
            return

        last_seen_signature = sig

        wallet_address = latest_tx.get("wallet_address", "Unknown")
        token_name = latest_tx.get("token_name", "Unknown")
        usd_amount = latest_tx.get("usd_amount", "0")

        # Create embed
        embed = discord.Embed(
            title="🟢 NEW BUY ALERT!",
            description=(
                f"👤 **Buyer:** [View Wallet](https://solscan.io/address/{wallet_address})\n"
                f"🪙 **Token:** `{token_name}`\n"
                f"💵 **Total Value:** `${usd_amount}`"
            ),
            color=discord.Color.green()
        )

        # Set image (replace with a reliable image link)
        embed.set_image(url="https://scontent.fkun1-2.fna.fbcdn.net/v/t39.30808-6/309910425_190715603352268_1954213668689896887_n.jpg?_nc_cat=101&ccb=1-7&_nc_sid=6ee11a&_nc_ohc=wQqYsgpTnEAQ7kNvwEES1Is&_nc_oc=AdmALa_7ec36fguGqbiCAycN4zmLg-voCIcaJhxAaTnXX5YFW576gYTR2_BmUh5y8t4&_nc_zt=23&_nc_ht=scontent.fkun1-2.fna&_nc_gid=hsfifyaIPi0x_7etLMMK9g&oh=00_AfFcfMlPDsJja4NkhWCqME6c5fqCnr3BD60iQxmQbMjbKw&oe=67FDA704")

        print(f"📢 Sending embed to Discord...", flush=True)

        channel = await bot.fetch_channel(CHANNEL_ID)
        await channel.send(embed=embed)

        print(f"✅ Sent Moralis alert for tx {sig}", flush=True)

    except Exception as e:
        print(f"❌ Error in check_moralis_transactions: {e}", flush=True)

# TikTok API setup
TIKTOK_API_HOST = "tiktok-api23.p.rapidapi.com"
TIKTOK_API_KEY = "69ecd569acmsh0109968293cfa28p19897ajsn7c400e914f77"
TIKTOK_SECUID = "MS4wLjABAAAAdaVuQdxR3JHOW8qSXEXZleD6Fv0eqmihFo1OWZ-PimB_SHSa6v3xLOnLyKi4JxcW"

headers = {
    "x-rapidapi-key": TIKTOK_API_KEY,
    "x-rapidapi-host": TIKTOK_API_HOST,
}

last_video_id = None

def fetch_latest_tiktok():
    url = f"https://{TIKTOK_API_HOST}/api/user/posts?secUid={TIKTOK_SECUID}&count=1&cursor=0"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        parsed = response.json()

        items = parsed.get("data", {}).get("itemList", [])
        if not items:
            return None

        latest = items[0]
        post_id = latest.get("id")
        desc = latest.get("desc", "No description")
        create_time = latest.get("createTime")
        post_url = f"https://www.tiktok.com/@maybachidze__/video/{post_id}"

        if "video" in latest and latest["video"].get("duration", 0) > 0:
            post_type = "🎥 Video"
        elif "imagePost" in latest:
            post_type = "🖼️ Photo Post"
        else:
            post_type = "📢 Post"

        return {
            "id": post_id,
            "desc": desc,
            "create_time": create_time,
            "video_url": post_url,
            "type": post_type
        }
    except Exception as e:
        print(f"❌ Failed to fetch or parse TikTok API response: {e}")
        return None



@tasks.loop(minutes=10)
async def check_tiktok_upload():
    global last_video_id

    print("🔁 Checking TikTok for new uploads...", flush=True)
    latest_post = fetch_latest_tiktok()

    if latest_post and latest_post["id"] != last_video_id:
        last_video_id = latest_post["id"]
        print(f"📹 New TikTok found: {latest_post['video_url']}", flush=True)

        for guild in bot.guilds:
            for category in guild.categories:
                if category.name.lower() == "news":
                    for channel in category.text_channels:
                        if channel.name == "maybach-content":
                            embed = discord.Embed(
                                title=f"💥NEW TIKTOK UPLOADED!💥",
                                description=latest_post["desc"],
                                url=latest_post["video_url"],
                                color=discord.Color.purple()
                            )
                            embed.add_field(name="Watch it here:", value=latest_post["video_url"], inline=False)
                            embed.set_footer(text="Posted by @maybachidze__")

                            await channel.send(embed=embed)
                            return




@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})", flush=True)
    check_moralis_transactions.start()
    check_tiktok_upload.start()
    for guild in bot.guilds:
        print(f"📌 Connected to guild: {guild.name} (ID: {guild.id})", flush=True)
        for channel in guild.text_channels:
            print(f"   └─ 💬 {channel.name} (ID: {channel.id})", flush=True)

bot.run(DISCORD_TOKEN)



