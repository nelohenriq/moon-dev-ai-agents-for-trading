import requests
from datetime import datetime, timedelta
from termcolor import cprint
import pandas as pd
import os

DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"
DEXSCREENER_URL = "https://dexscreener.com/solana/"
DEXS = ["raydium", "orca", "lifinity", "phoenix", "meteora", "step"]


def fetch_token_pools(token_address):
    """Fetch pools for a specific token from DEX Screener."""
    url = f"{DEXSCREENER_API}/{token_address}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("pairs", [])
    return []


def analyze_migrated_tokens(token_address):
    """Check if the token migrated to Raydium by comparing past pools on other DEXs."""
    pools = fetch_token_pools(token_address)

    if not pools:
        print(f"No pools found for {token_address}")
        return

    raydium_pool = None
    other_dex_pools = []

    for pair in pools:
        dex_id = pair.get("dexId", "").lower()
        timestamp = pair.get("pairCreatedAt", 0)

        # Check if timestamp is in milliseconds (e.g., more than 10 digits)
        if timestamp > 1e10:
            timestamp = timestamp / 1000

        creation_time = datetime.fromtimestamp(timestamp)

        # Calculate one hour ago
        one_hour_ago = datetime.now() - timedelta(hours=1)

        # Check if the token was created within the last hour
        dexscreener_url = DEXSCREENER_URL + token_address
        if creation_time >= one_hour_ago:
            cprint(
                f"New token {dexscreener_url} detected on {dex_id} created at {creation_time}",
                "green",
            )
        else:
            cprint(f"Token on {dex_id} is older than one hour", "yellow")

        pool_data = {
            "dex": dex_id,
            "pair_address": pair.get("pairAddress", ""),
            "liquidity_usd": pair.get("liquidity", {}).get("usd", 0),
            "volume_24h": pair.get("volume", {}).get("h24", 0),
            "creation_time": creation_time,
        }

        if "raydium" in dex_id:
            raydium_pool = pool_data
        else:
            other_dex_pools.append(pool_data)

    # If there is a new Raydium pool but it existed elsewhere, it's likely a migration
    if raydium_pool and other_dex_pools:
        previous_pools = sorted(
            other_dex_pools, key=lambda x: x["creation_time"] or datetime.min
        )
        first_pool = previous_pools[0] if previous_pools else None

        if first_pool and raydium_pool["creation_time"]:
            migration_detected = (
                first_pool["creation_time"] < raydium_pool["creation_time"]
            )
        else:
            migration_detected = False

        return {
            "token_address": token_address,
            "new_raydium_pool": raydium_pool,
            "previous_pools": previous_pools,
            "migration_detected": migration_detected,
        }

    return None


def discover_new_raydium_pools():
    """Fetch newly created Raydium pools and check if they migrated from other DEXs."""
    token_list = [
        "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
        "ksoBzfw5PPWYdjRtgMfkyxNnqHJ3EWSf1XoAWXYFVce",
        "F775NjaSmqSZTbCs8jcj899rZn5W3v32QyFbg877pump",
        "Avy1abPkJKJdadFVieTuF8oeN6ZFWsKNtKzU1a8tgn6Z",
    ]  # Replace with dynamically fetched token addresses
    migrations = []

    for token in token_list:
        result = analyze_migrated_tokens(token)
        if result and result["migration_detected"]:
            migrations.append(result)

    if migrations:
        df = pd.DataFrame(migrations)
        os.makedirs("moondev/src/data", exist_ok=True)
        df.to_csv("moondev/src/data/migrated_tokens.csv", index=False)
        print(f"Detected {len(migrations)} migrated tokens.")

    return migrations


discover_new_raydium_pools()
