"""
🌙 Moon Dev's OHLCV Data Collector
Collects Open-High-Low-Close-Volume data for specified tokens
Built with love by Moon Dev 🚀
"""

from src.config import *
from src import nice_funcs as n
import pandas as pd
from datetime import datetime
import os
from termcolor import colored, cprint
import time


def collect_token_data(
    contract_address, days_back=DAYSBACK_4_DATA, timeframe=DATA_TIMEFRAME
):
    """Collect OHLCV data for a single token"""
    cprint(
        f"\n🤖 Moon Dev's AI Agent fetching data for {contract_address}...",
        "white",
        "on_blue",
    )

    try:
        # Get data from CoinGecko
        data = n.get_data(contract_address, days_back, timeframe)

        if data is None or data.empty:
            cprint(
                f"❌ Moon Dev's AI Agent couldn't fetch data for {contract_address}",
                "white",
                "on_red",
            )
            return None

        cprint(
            f"📊 Moon Dev's AI Agent processed {len(data)} candles for analysis",
            "white",
            "on_blue",
        )

        # Save data if configured
        if SAVE_OHLCV_DATA:
            save_path = f"moondev/src/data/{contract_address}_latest.csv"
        else:
            save_path = f"temp_data/{contract_address}_latest.csv"

        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save to CSV
        data.to_csv(save_path)
        cprint(
            f"💾 Moon Dev's AI Agent cached data for {contract_address[:4]}",
            "white",
            "on_green",
        )

        return data

    except Exception as e:
        cprint(
            f"❌ Moon Dev's AI Agent encountered an error: {str(e)}", "white", "on_red"
        )
        return None


def collect_all_tokens():
    """Collect OHLCV data for all monitored tokens"""
    market_data = {}

    cprint(
        "\n🔍 Moon Dev's AI Agent starting market data collection...",
        "white",
        "on_blue",
    )

    for contract_address in MONITORED_TOKENS:
        data = collect_token_data(contract_address)
        if data is not None:
            market_data[contract_address] = data
            time.sleep(6)  # Add a delay to avoid rate limiting

    cprint(
        "\n✨ Moon Dev's AI Agent completed market data collection!",
        "white",
        "on_green",
    )

    return market_data


if __name__ == "__main__":
    try:
        collect_all_tokens()
    except KeyboardInterrupt:
        print("\n👋 Moon Dev OHLCV Collector shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("🔧 Moon Dev suggests checking the logs and trying again!")
