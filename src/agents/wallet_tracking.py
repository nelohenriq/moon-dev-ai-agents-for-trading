import csv
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Data paths
DATA_FOLDER = Path(__file__).parent.parent / "data"
SNIPER_DATA = DATA_FOLDER / "sniper_agent" / "recent_tokens.csv"
WALLET_TRACKING_FILE = DATA_FOLDER / "wallet_tracking" / "tracked_wallets.csv"
ANALYZED_TX_DATA = DATA_FOLDER / "tx_agent" / "analyzed_transactions.csv"

# RPC Endpoint
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT")

# Load analyzed transactions cache
def load_analyzed_transactions():
    """Load analyzed transactions from cache."""
    if not ANALYZED_TX_DATA.exists():
        return set()

    with open(ANALYZED_TX_DATA, newline="") as csvfile:
        reader = csv.reader(csvfile)
        return {tuple(row) for row in reader if row}  # Store as a set of tuples

# Check if transaction was already analyzed
def is_transaction_analyzed(wallet_address, token_address):
    """Check if a wallet's transaction for a token has been analyzed."""
    return (wallet_address, token_address) in analyzed_tx_cache

# Save new transaction analysis to cache
def save_analyzed_transaction(wallet_address, token_address):
    """Save analyzed transactions to cache and persist to file."""
    if not is_transaction_analyzed(wallet_address, token_address):
        analyzed_tx_cache.add((wallet_address, token_address))  # Update in-memory cache
        with open(ANALYZED_TX_DATA, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([wallet_address, token_address])  # Append new entry

# Fetch token holders using getTokenLargestAccounts
def get_token_holders(token_address):
    payload = {
        "jsonrpc": "2.0",
        "id": "getTokenLargestAccounts",
        "method": "getTokenLargestAccounts",
        "params": [token_address],
    }
    response = requests.post(RPC_ENDPOINT, json=payload)
    if response.status_code == 200:
        data = response.json().get("result", {}).get("value", [])
        return [(holder["address"], float(holder["amount"])) for holder in data]
    return []

# Fetch all token accounts by wallet
def get_token_accounts_by_owner(wallet_address, token_mint_address):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_address,
            {
                "mint": token_mint_address,  # Filter by mint address
                "encoding": "jsonParsed"
            }
        ]
    }
    response = requests.post(RPC_ENDPOINT, json=payload)
    
    if response.status_code == 200:
        data = response.json().get("result", {}).get("value", [])
        return [account["account"]["data"]["parsed"]["info"]["mint"] for account in data]
    return []

# Load token addresses from the sniper agent's recent_tokens.csv
def load_recent_tokens():
    if not SNIPER_DATA.exists():
        print("❌ No recent token data found.")
        return []
    
    with open(SNIPER_DATA, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip the header row
        return [row[0] for row in reader if row]

# Track wallets investing in newly sniped tokens
def track_wallets():
    tokens = load_recent_tokens()
    if not tokens:
        return

    wallet_data = []
    for token in tokens:
        print(f"🔍 Tracking holders for token: {token}")
        holders = get_token_holders(token)
        
        for address, amount in holders:
            if is_transaction_analyzed(address, token):
                print(f"✅ Skipping already analyzed wallet: {address} for token: {token}")
                continue
            
            # Fetch mints held by the wallet
            mint_addresses = get_token_accounts_by_owner(address, "T5Hy2dMwCKhJLQ7rPpBNSCdP3UbuBTVRefYMC7h6iFC")
            
            for mint in mint_addresses if mint_addresses else []:
                wallet_data.append([address, mint, amount])
                save_analyzed_transaction(address, mint)
    
    # Save wallet tracking data
    WALLET_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WALLET_TRACKING_FILE, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["wallet_address", "token_address", "amount"])
        writer.writerows(wallet_data)
    print(f"✅ Wallet tracking data saved to {WALLET_TRACKING_FILE}")

# Load cache at script start
analyzed_tx_cache = load_analyzed_transactions()

if __name__ == "__main__":
    track_wallets()
