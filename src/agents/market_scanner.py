from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import requests
import os

load_dotenv()

DEXSCREENER_API = os.getenv("DEXSCREENER_API")


def get_high_growth_tokens(min_mcap=100_000_000, growth_days=30):
    current_time = datetime.now()
    dex_data = requests.get(f"{DEXSCREENER_API}/pairs").json()
    growth_tokens = []

    for pair in dex_data["pairs"]:
        creation_time = datetime.fromtimestamp(pair["baseToken"].get("createdAt", 0))
        age_days = (current_time - creation_time).days

        if age_days <= growth_days:
            price = float(pair.get("priceUsd", 0))
            supply = float(pair.get("baseToken", {}).get("totalSupply", 0))
            market_cap = price * supply

            if market_cap >= min_mcap:
                growth_tokens.append(
                    {
                        "address": pair["baseToken"]["address"],
                        "symbol": pair["baseToken"]["symbol"],
                        "market_cap": market_cap,
                        "age_days": age_days,
                        "volume_24h": pair.get("volume", {}).get("h24", 0),
                        "discovery_date": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

    # Save to CSV
    df = pd.DataFrame(growth_tokens)
    output_path = "src/data/high_growth_tokens.csv"
    df.to_csv(output_path, index=False)

    return growth_tokens


if __name__ == "__main__":
    tokens = get_high_growth_tokens()
    print(f"Found {len(tokens)} high growth tokens")
