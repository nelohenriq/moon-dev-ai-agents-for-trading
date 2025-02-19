"""
🌙 Moon Dev's Solana Analysis Agent - Built with love by Moon Dev 🚀
Analyzes token launches and transactions to find the best opportunities!
"""

import os
import sys
from pathlib import Path
import pandas as pd
import time
import requests
import logging
from rich.console import Console
from rich import print as rprint
from dotenv import load_dotenv
from termcolor import colored
import random
from src.nice_funcs import token_security_info, token_creation_info, token_price

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

# Load environment variables
load_dotenv()

# Suppress ALL logs except critical
logging.getLogger().setLevel(logging.CRITICAL)

# Initialize Rich console
console = Console()

# Analysis Constants
CHECK_INTERVAL = 600  # 5 minutes between each analysis run
MIN_MARKET_CAP = 1000  # Minimum market cap in USD
MAX_MARKET_CAP = 1000000  # Maximum market cap in USD (10M)
MIN_LIQUIDITY = 1000  # Minimum liquidity in USD
MAX_LIQUIDITY = 500000  # Maximum liquidity in USD (500k)
MIN_VOLUME_24H = 5000  # Minimum 24h volume
MAX_TOP_HOLDERS_PCT = 60  # Maximum percentage held by top 10 holders
MIN_UNIQUE_HOLDERS = 100  # Minimum number of unique holders
MIN_AGE_HOURS = 1  # Minimum token age in hours
MAX_AGE_HOURS = 48  # Maximum token age in hours
MIN_BUY_TX_PCT = 60  # Minimum percentage of buy transactions
MIN_TRADES_LAST_HOUR = 10  # Minimum number of trades in last hour

# Display Constants
AUTO_OPEN_BROWSER = True  # Set to True to automatically open new tokens in browser
USE_DEXSCREENER = True  # Set to True to use DexScreener instead of Birdeye

BACKGROUND_COLORS = [
    "on_blue",
    "on_magenta",
    "on_cyan",
    "on_green",
    "on_yellow",  # Removed white for better readability
]

ANALYSIS_EMOJIS = [
    "🔍",
    "📊",
    "📈",
    "🎯",
    "💎",  # Analysis & targets
    "🚀",
    "⭐",
    "🌟",
    "✨",
    "💫",  # Moon Dev specials
    "🎨",
    "🎭",
    "🎪",
    "🎢",
    "🎡",  # Fun stuff
]

# Data paths
DATA_FOLDER = Path(__file__).parent.parent / "data"
SNIPER_DATA = DATA_FOLDER / "sniper_agent" / "recent_tokens.csv"
TX_DATA = DATA_FOLDER / "tx_agent" / "recent_transactions.csv"
TOP_PICKS_FILE = DATA_FOLDER / "solana_agent" / "top_picks.csv"

RPC_ENDPOINT = (
    "https://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"
)


class SolanaAnalyzer:
    def __init__(self):
        """🌙 Moon Dev's Solana Analyzer - Built with love by Moon Dev 🚀"""
        self.api_key = os.getenv("MOONDEV_API_KEY")
        self.headers = {"X-API-Key": self.api_key} if self.api_key else {}
        self.session = requests.Session()

        # Create data directory if it doesn't exist
        (DATA_FOLDER / "solana_agent").mkdir(parents=True, exist_ok=True)

    def token_overview(self, address):
        """
        Fetch token overview using Helius RPC for metadata and DEX Screener for market data.
        """
        print(f"Getting the token overview for {address}")
        result = {}

        try:
            # 1️⃣ Get token metadata using Helius RPC
            payload_metadata = {
                "jsonrpc": "2.0",
                "id": "getAccountInfo",
                "method": "getAccountInfo",
                "params": [address, {"encoding": "jsonParsed"}],
            }
            metadata_response = requests.post(RPC_ENDPOINT, json=payload_metadata)

            if metadata_response.status_code == 200:
                metadata = (
                    metadata_response.json()
                    .get("result", {})
                    .get("value", {})
                    .get("data", {})
                    .get("parsed", {})
                )
                if metadata:
                    result["decimals"] = metadata.get("info", {}).get("decimals", 9)
                    result["freezeAuthority"] = metadata.get("info", {}).get(
                        "freezeAuthority"
                    )
                    result["isInitialized"] = metadata.get("info", {}).get(
                        "isInitialized"
                    )
                    result["mintAuthority"] = metadata.get("info", {}).get(
                        "mintAuthority"
                    )
                    result["supply"] = int(metadata.get("info", {}).get("supply", 0))

            # 2️⃣ Get token security info using `getAsset`
            payload_security = {
                "jsonrpc": "2.0",
                "id": "getAsset",
                "method": "getAsset",
                "params": [address],
            }
            security_response = requests.post(RPC_ENDPOINT, json=payload_security)
            if security_response.status_code == 200:
                security_data = security_response.json().get("result", {})
                result["security"] = security_data

            # 3️⃣ Get market data from DEX Screener
            dex_screener_url = (
                f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            )
            dex_response = requests.get(dex_screener_url)

            # Check if DEX Screener returned valid data
            if dex_response.status_code != 200:
                print(
                    f"❌ Failed to fetch DEX Screener data for {address}. Skipping token."
                )
                return None

            dex_data = dex_response.json().get("pairs", None)

            # If no trading pairs exist, the token is dead → SKIP
            if not dex_data:
                print(
                    f"❌ No trading data on DEX Screener for {address}. Token is likely dead. Skipping."
                )
                return None

            # Extract top market data
            top_market = dex_data[0]
            result["liquidity"] = float(top_market.get("liquidity", {}).get("usd", 0))
            result["mc"] = float(top_market.get("fdv", 0))
            result["v24USD"] = float(top_market.get("volume", {}).get("h24", 0))
            result["trade1h"] = int(
                top_market.get("txns", {}).get("h1", {}).get("buys", 0)
                + top_market.get("txns", {}).get("h1", {}).get("sells", 0)
            )
            result["buy_percentage"] = (
                float(top_market.get("txns", {}).get("h1", {}).get("buys", 0))
                / max(1, result["trade1h"])
                * 100
            )

            return result

        except Exception as e:
            print(f"❌ Error retrieving token overview for {address}: {str(e)}")
            return None

    def analyze_token(self, token_address):
        """Analyze a single token using Moon Dev's criteria"""
        try:
            print(f"\n🔍 Fetching overview for {token_address}")

            # Initialize variables
            top_holders_pct = 100  # Default if we can't get the data
            reasons = []  # Track rejection reasons

            # Get token overview data
            overview = self.token_overview(token_address)

            # ✅ Handle missing overview data
            if overview is None:
                print(f"⚠️ Skipping {token_address}: No valid token overview data.")
                return None

            # ✅ Extract security info from overview
            security_info = overview.get("security", {})

            # Extract relevant security metrics
            top_holders_pct = security_info.get("top10HolderPercent", 1) * 100
            liquidity_locked = security_info.get("liquidityLocked", False)
            mint_authority = security_info.get("mintAuthority", None)
            freeze_authority = security_info.get("freezeAuthority", None)

            print(f"\n🔒 Security Info for {token_address[:8]}:")
            print(f"👥 Top 10 Holders: {top_holders_pct:.1f}%")
            print(f"🔒 Liquidity Locked: {liquidity_locked}")
            print(f"🛠️ Mint Authority: {mint_authority}")
            print(f"❄️ Freeze Authority: {freeze_authority}")

            # **Security Filters**
            if top_holders_pct > MAX_TOP_HOLDERS_PCT:
                reasons.append(f"High holder concentration ({top_holders_pct:.1f}%)")

            if not liquidity_locked:
                reasons.append("Liquidity is not locked")

            if mint_authority:
                reasons.append("Mint authority still exists")

            if freeze_authority:
                reasons.append("Freeze authority is enabled")

            # ✅ Market and Volume Checks
            liquidity = float(overview.get("liquidity", 0))
            market_cap = float(overview.get("mc", 0))
            volume_24h = float(overview.get("v24USD", 0))
            trades_1h = float(overview.get("trade1h", 0))
            buy_percentage = float(overview.get("buy_percentage", 0))

            print(f"\n💰 Market Cap: ${market_cap:,.2f}")
            print(f"💧 Liquidity: ${liquidity:,.2f}")
            print(f"📊 24h Volume: ${volume_24h:,.2f}")
            print(f"🔄 1h Trades: {trades_1h}")
            print(f"📈 Buy Ratio: {buy_percentage:.1f}%")

            if market_cap < MIN_MARKET_CAP:
                reasons.append(f"Market cap too low (${market_cap:,.2f})")

            if market_cap > MAX_MARKET_CAP:
                reasons.append(f"Market cap too high (${market_cap:,.2f})")

            if liquidity < MIN_LIQUIDITY:
                reasons.append(f"Low liquidity (${liquidity:,.2f})")

            if liquidity > MAX_LIQUIDITY:
                reasons.append(f"Liquidity too high (${liquidity:,.2f})")

            if volume_24h < MIN_VOLUME_24H:
                reasons.append(f"Low 24h volume (${volume_24h:,.2f})")

            if trades_1h < MIN_TRADES_LAST_HOUR:
                reasons.append(f"Low 1h trades ({trades_1h})")

            if buy_percentage < MIN_BUY_TX_PCT:
                reasons.append(f"Low buy ratio ({buy_percentage:.1f}%)")

            # ✅ Log rejections and return None if any condition fails
            if reasons:
                print(f"\n🚫 Token {token_address[:8]} rejected due to:")
                for reason in reasons:
                    print(f"   ❌ {reason}")
                return None

            # ✅ Return token data if all checks pass
            return {
                "token_address": token_address,
                "market_cap": market_cap,
                "liquidity": liquidity,
                "volume_24h": volume_24h,
                "trades_1h": trades_1h,
                "buy_percentage": buy_percentage,
                "top_holders_pct": top_holders_pct,
                "liquidity_locked": liquidity_locked,
                "mint_authority": mint_authority,
                "freeze_authority": freeze_authority,
            }

        except Exception as e:
            print(f"⚠️ Error analyzing token {token_address[:8]}: {str(e)}")
            return None

    def get_token_link(self, token_address):
        """Get the appropriate link based on settings"""
        if USE_DEXSCREENER:
            return f"https://dexscreener.com/solana/{token_address}"
        else:
            return f"https://birdeye.so/token/{token_address}?chain=solana"

    def update_top_picks(self, new_results):
        """Update the top picks CSV with new results"""
        try:
            # Create new DataFrame with timestamp
            new_df = pd.DataFrame(new_results)
            new_df["found_at"] = pd.Timestamp.now()

            # Load existing top picks if file exists
            if TOP_PICKS_FILE.exists():
                existing_picks = pd.read_csv(TOP_PICKS_FILE)

                # Continue with existing update logic
                combined = pd.concat([existing_picks, new_df])
                combined = combined.drop_duplicates(
                    subset=["token_address"], keep="last"
                )

                # Sort by metrics (you can adjust these weights)
                combined["score"] = (
                    combined["liquidity"] * 0.3
                    + combined["volume_24h"] * 0.2
                    + combined["trades_1h"] * 0.2
                    + combined["buy_percentage"] * 0.1
                    + (combined["market_cap"] / MAX_MARKET_CAP) * 0.2
                )

                # Keep top 50 by score
                top_picks = combined.nlargest(50, "score")

                # Drop the score column before saving
                top_picks = top_picks.drop("score", axis=1)

            else:
                # If no existing file, use new results directly
                top_picks = new_df

            # Open browser for all tokens that passed filters
            if AUTO_OPEN_BROWSER and not new_df.empty:
                print(f"\n🌟 Opening {len(new_df)} filtered tokens in browser...")
                for token in new_df["token_address"]:
                    try:
                        import webbrowser

                        link = self.get_token_link(token)
                        webbrowser.open(link)
                        time.sleep(0.5)  # Small delay between opens
                    except Exception as e:
                        print(f"⚠️ Error opening browser for {token[:8]}: {str(e)}")

            # Save updated top picks
            top_picks.to_csv(TOP_PICKS_FILE, index=False)
            print(f"\n🌟 Updated top picks file with {len(top_picks)} tokens!")

        except Exception as e:
            print(f"⚠️ Error updating top picks: {str(e)}")

    def save_analysis(self, results, source):
        """Save analysis results and update top picks"""
        try:
            if results:
                # Save source-specific analysis
                df = pd.DataFrame(results)
                save_path = DATA_FOLDER / f"{source}_analysis.csv"
                print(f"\n📂 Saving results to {save_path}...")
                df.to_csv(save_path, index=False)
                print(f"\n💫 Saved {source} analysis with {len(df)} filtered tokens")
                print(df.head())  # Print first few rows to verify

                # Update top picks with new results
                self.update_top_picks(results)

        except Exception as e:
            print(f"⚠️ Error saving analysis: {str(e)}")

    def display_top_pick(self, token_data):
        """Display a top pick with Moon Dev style 🌙"""
        random_emoji = random.choice(ANALYSIS_EMOJIS)
        random_bg = random.choice(BACKGROUND_COLORS)

        print(
            f"\n{colored(f'{random_emoji} MOON DEV AI AGENT TOP PICK', 'white', random_bg)}"
        )
        print(f"Token: {token_data['token_address']}")
        print(f"💰 Market Cap: ${token_data['market_cap']:,.2f}")
        print(f"💧 Liquidity: ${token_data['liquidity']:,.2f}")
        print(f"📊 24h Volume: ${token_data['volume_24h']:,.2f}")
        print(f"🔄 1h Trades: {token_data['trades_1h']}")
        print(f"📈 Buy Ratio: {token_data['buy_percentage']:.1f}%")
        print(f"👥 Top Holders: {token_data['top_holders_pct']:.1f}%")
        print(f"💵 Current Price: ${token_data['price']:,.8f}")

        # Add appropriate link based on settings
        link = self.get_token_link(token_data["token_address"])
        print(f"🔍 {'DexScreener' if USE_DEXSCREENER else 'Birdeye'}: {link}")
        print("=" * 50)

    def analyze_tokens(self, df):
        """Analyze token data with metrics"""
        results = []

        # Standardize column name - handle all possible formats
        if "Token Address" in df.columns:
            # Sniper agent format
            df = df.rename(columns={"Token Address": "token_address"})
        elif "contract_address" in df.columns:
            # Transaction agent format
            df = df.rename(columns={"contract_address": "token_address"})
        elif "birdeye_link" in df.columns:
            # Extract from birdeye link if no direct address column
            df["token_address"] = df["birdeye_link"].apply(
                lambda x: (
                    x.split("/token/")[1].split("?")[0] if isinstance(x, str) else None
                )
            )

        if "token_address" not in df.columns:
            print("⚠️ Could not find token address column in data")
            return results

        # Clean the dataframe - remove rows with invalid token addresses
        df = df.dropna(
            subset=["token_address"]
        )  # Remove rows where token_address is NaN
        df = df[
            df["token_address"].astype(str).str.len() > 30
        ]  # Basic validation for Solana addresses

        # Debug print to verify data
        print(f"\n🔍 Processing {len(df)} valid tokens from data source")
        print(f"Columns found: {df.columns.tolist()}")

        for _, row in df.iterrows():
            try:
                token_address = str(row["token_address"]).strip()
                if not token_address or token_address.lower() == "nan":
                    continue

                token_data = self.analyze_token(token_address)
                if token_data:
                    results.append(token_data)
                    self.display_top_pick(token_data)
                    time.sleep(1)  # Slight delay between displays
            except Exception as e:
                print(f"⚠️ Error processing token: {str(e)}")
                continue

        return results

    def run_analysis(self):
        """Main analysis loop"""
        print("\n🔍 Starting Moon Dev's AI Analysis Agent...")

        while True:
            try:
                # Analyze sniper tokens if file exists
                if SNIPER_DATA.exists():
                    print("\n📊 Analyzing Sniper Agent tokens...")
                    tokens_df = pd.read_csv(SNIPER_DATA)
                    results = self.analyze_tokens(tokens_df)
                    print(
                        f"\n🔍 Sniper analysis results count: {len(results) if results else 0}"
                    )
                    self.save_analysis(results, "sniper")

                # Analyze transactions if file exists
                if TX_DATA.exists():
                    print("\n📊 Analyzing Transaction Agent tokens...")
                    tx_df = pd.read_csv(TX_DATA)
                    results = self.analyze_tokens(tx_df)
                    self.save_analysis(results, "transactions")

            except Exception as e:
                print(f"⚠️ Error in analysis loop: {str(e)}")

            print(
                f"\n😴 Moon Dev's AI Agent sleeping for {CHECK_INTERVAL/60:.1f} minutes..."
            )
            time.sleep(CHECK_INTERVAL)


def main():
    """Main entry point"""
    analyzer = SolanaAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
