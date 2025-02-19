import csv
import requests
from pathlib import Path

# Data paths
DATA_FOLDER = Path(__file__).parent.parent / "data"
SNIPER_DATA = DATA_FOLDER / "sniper_agent" / "recent_tokens.csv"
WALLET_TRACKING_FILE = DATA_FOLDER / "wallet_tracking" / "tracked_wallets.csv"
ANALYZED_TX_DATA = DATA_FOLDER / "tx_agent" / "analyzed_transactions.csv"

# RPC Endpoint
RPC_ENDPOINT = (
    "https://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"
)


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


def get_token_holders(token_address):
    """Fetch token holders using getTokenLargestAccounts RPC call."""
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


def load_recent_tokens():
    """Load token addresses from the sniper agent's recent_tokens.csv."""
    if not SNIPER_DATA.exists():
        print("❌ No recent token data found.")
        return []

    with open(SNIPER_DATA, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip the header row
        return [row[0] for row in reader if row]


def track_wallets():
    """Track wallets investing in newly sniped tokens."""
    tokens = load_recent_tokens()
    if not tokens:
        return

    wallet_data = []
    for token in tokens:
        print(f"🔍 Tracking holders for token: {token}")
        holders = get_token_holders(token)

        for address, amount in holders:
            if is_transaction_analyzed(address, token):
                print(
                    f"✅ Skipping already analyzed wallet: {address} for token: {token}"
                )
                continue

            wallet_data.append([address, token, amount])
            save_analyzed_transaction(address, token)  # Mark as analyzed

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
