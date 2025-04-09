import requests
import json

# Your API request URL and headers
url = "https://solana-gateway.moralis.io/token/mainnet/Dj3wnBYJZGnzMkGGyUqLbtyU1bt4CaFF9mES44Nhpump/swaps?order=DESC"
headers = {
    "Accept": "application/json",
    "X-API-Key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjExYjQ4YjQ4LWJhYjgtNDJkOC1iNzEyLTVhZWYwZWY0NGU1NiIsIm9yZ0lkIjoiNDQwODEwIiwidXNlcklkIjoiNDUzNTExIiwidHlwZUlkIjoiZTRmNzJlNWEtNmU5MS00NjRmLTg2NDktMDhiMzg5NzI0MTBhIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDQyMjQ3NzYsImV4cCI6NDg5OTk4NDc3Nn0.--O9_2uuC7l5xyg7CJ8Jktr0fuGbWfH8olLfbeKkqmI"
}

# Track the last seen transaction signature
last_seen_signature = None

def get_latest_buy():
    try:
        # Send the API request
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return None
        
        data = response.json()  # Parse JSON response
        
        # Check if we have transaction data
        if not data.get("result"):
            print("⚠️ No transactions found.")
            return None
        
        # Extract the latest transaction (first in the list)
        latest_tx = data["result"][0]
        
        return latest_tx
    
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def check_new_transaction():
    global last_seen_signature

    # Fetch the latest transaction details
    latest_tx = get_latest_buy()

    if not latest_tx:
        return

    # Get the transaction signature (used to identify uniqueness)
    sig = latest_tx.get("signature")

    if sig == last_seen_signature:
        print("⏳ No new purchases.")
        return

    # Update the last seen signature
    last_seen_signature = sig

    # Extract transaction details
    buyer = latest_tx.get("from", "Unknown")
    amount = latest_tx.get("amount", 0)  # Assuming 'amount' field holds the purchased amount
    usd_value = latest_tx.get("usd_value", 0.0)
    tx_link = f"https://solscan.io/tx/{sig}"

    # Print the new purchase message
    msg = (
        f"🚀 **New Purchase Detected!**\n"
        f"👤 Buyer: `{buyer[:4]}...{buyer[-4:]}`\n"
        f"💰 Amount: {amount} tokens (~${usd_value:.2f})\n"
        f"[🔗 View on Solscan]({tx_link})"
    )

    print(msg)

# Check for new transactions (e.g., every 30 seconds)
import time
while True:
    check_new_transaction()
    time.sleep(30)  # Wait for 30 seconds before checking again
