import logging
import os
import pandas as pd
import requests
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv

load_dotenv()
RPC_ENDPOINT = os.getenv('RPC_ENDPOINT')

# Set up logging with emojis
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def log_info(msg):
    logging.info(f"🔍 {msg}")

def log_warning(msg):
    logging.warning(f"⚠️ {msg}")

def log_error(msg):
    logging.error(f"❌ {msg}")

def get_token_owner_address(token_address):
    """
    Retrieve the owner address for a given token address using Helius getAsset method.

    Args:
    - token_address (str): The token address to look up.

    Returns:
    - str: The owner address if found, otherwise None.
    """
    try:
        # Prepare payload to query the Helius API for asset info
        payload = {
            "jsonrpc": "2.0",
            "method": "getAsset",
            "params": {
                "id": token_address
            },
            "id": "token-owner-fetch"
        }

        # Make the RPC call to Helius
        response = requests.post(RPC_ENDPOINT, headers={"Content-Type": "application/json"}, json=payload)
        data = response.json()

        if "result" in data:
            # Extract owner address from the response
            authorities = data["result"].get("authorities", [])
            if authorities:
                # The first authority is typically the creator/owner
                owner_address = authorities[0].get("address")
                if owner_address:
                    return owner_address
                else:
                    log_warning(f"Owner address not found in authorities for token {token_address}.")
            else:
                log_warning(f"No authorities found for token {token_address}.")
        else:
            log_warning(f"Failed to fetch asset data for token {token_address}.")
        return None

    except Exception as e:
        log_error(f"Error fetching owner address for token {token_address}: {e}")
        return None


def get_high_growth_tokens(token_addresses, min_mcap=100_000):
    current_time = datetime.now()
    growth_tokens = []

    log_info("Fetching tokens from RPC endpoint...")

    for token_address in token_addresses:
        # Get the owner address for each token address dynamically
        owner_address = get_token_owner_address(token_address)

        if owner_address:
            search_payload = {
                "jsonrpc": "2.0",
                "id": "token-search",
                "method": "searchAssets",
                "params": {
                    "tokenType": "fungible",
                    "owner_address": owner_address,  # Use the obtained owner address
                    "page": 1,
                    "limit": 100,
                    "options": {
                        "showNativeBalance": True,
                        "showCollectionMetadata": True
                    }
                }
            }

            tokens_response = requests.post(RPC_ENDPOINT, json=search_payload)
            tokens = tokens_response.json().get('result', {}).get('items', [])

            log_info(f"🔎 Found {len(tokens)} tokens for owner {owner_address}. Filtering based on market cap...")

            for token in tokens:
                token_address = token['id']
                
                # Get token info using getAccountInfo like in whales.py
                token_info_payload = {
                    "jsonrpc": "2.0",
                    "id": "token-info",
                    "method": "getAccountInfo",
                    "params": [token_address, {"encoding": "jsonParsed"}],
                }

                token_info = requests.post(RPC_ENDPOINT, json=token_info_payload).json()

                if 'result' in token_info and token_info['result']:
                    try:
                        supply = float(token_info['result']['value']['data']['parsed']['info']['supply'])
                        price = float(token.get('price', 0))
                        market_cap = price * supply

                        if market_cap >= min_mcap:
                            growth_tokens.append({
                                "address": token_address,
                                "symbol": token.get('symbol', ''),
                                "market_cap": market_cap,
                                "volume_24h": token.get('volume24h', 0),
                                "discovery_date": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "owner_address": owner_address
                            })
                            log_info(f"🚀 {token.get('symbol', 'Unknown')} added! Market Cap: ${market_cap:,.0f}")

                    except Exception as e:
                        log_error(f"Error processing token {token_address}: {e}")

    df = pd.DataFrame(growth_tokens)
    if not df.empty:
        df.to_csv("moondev/src/data/high_growth_tokens.csv", index=False)
        log_info("📁 Data saved to src/data/high_growth_tokens.csv")
        return growth_tokens
    else:
        log_warning("No high-growth tokens found.")
        return None

if __name__ == "__main__":
    try:
        # Automatically load token addresses from the CSV (recent tokens)
        df = pd.read_csv("moondev/src/data/sniper_agent/recent_tokens.csv")  # Update the path if needed
        token_addresses = df['Token Address'].tolist()  # Get all token addresses as a list
    except Exception as e:
        log_error(f"Error reading token addresses from CSV: {e}")
        token_addresses = []

    if token_addresses:
        growth_tokens = get_high_growth_tokens(token_addresses)

        if growth_tokens:
            cprint(f"🎯 Found {len(growth_tokens)} high-growth tokens:", "green")
            for token in growth_tokens:
                cprint(
                    f"🔹 Address: {token['address']}", "white",
                    f"💰 Symbol: {token['symbol']}", "yellow",
                    f"📈 Market Cap: ${token['market_cap']:,}", "blue",
                    f"📊 Volume 24h: ${token['volume_24h']:,}", "magenta",
                    f"🕒 Discovery Date: {token['discovery_date']}", "green"
                )
        else:
            cprint("❌ No high-growth tokens found.", "red")
    else:
        log_warning("No token addresses found.")
