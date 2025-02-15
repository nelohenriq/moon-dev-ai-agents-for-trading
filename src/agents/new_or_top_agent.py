"""
🌙 Moon Dev's New & Top Coins Agent 🔍

=================================
📚 QUICK START GUIDE
=================================
1. Set up environment variables in .env:
   - COINGECKO_API_KEY
   - ANTHROPIC_KEY (for Claude)
   - DEEPSEEK_KEY (for DeepSeek)

2. Choose AI model by setting MODEL_OVERRIDE at top of file:
   ```python
   # Use config.py's AI_MODEL (Default)
   MODEL_OVERRIDE = "0"  
   
   # For DeepSeek Chat (Faster, more concise)
   MODEL_OVERRIDE = "deepseek-chat"  
   
   # For DeepSeek Reasoner (Better reasoning, more detailed)
   MODEL_OVERRIDE = "deepseek-reasoner"
   ```

   🔍 Model Comparison:
   - Claude (from config.py): Balanced analysis, good for general use
   - DeepSeek Chat: Faster responses, more concise analysis
   - DeepSeek Reasoner: Better for complex market analysis, 
     provides more detailed reasoning

   To switch models:
   1. Get your DeepSeek API key from: https://platform.deepseek.com
   2. Add it to .env as DEEPSEEK_KEY="your_key_here"
   3. Set MODEL_OVERRIDE to your preferred model
   4. Restart the agent

3. Run the agent:
   python src/agents/new_or_top_agent.py

4. Check results in src/data/coingecko_results:
   - top_gainers_losers.csv (Raw data of top performers)
   - new_coins.csv (Latest 200 added coins)
   - ai_picks.csv (AI analysis and recommendations)
   - ai_buys.csv (Only BUY recommendations)

The agent runs every hour and:
- Fetches top 30 gainers and losers
- Gets latest 200 new coins
- Analyzes each coin with AI
- Saves BUY/SELL/DO NOTHING recommendations

=================================
🤖 AI ANALYSIS PROMPT
=================================
You can modify this prompt to customize the AI analysis:
"""

AI_PROMPT = """
Please analyze this cryptocurrency and provide a clear BUY, SELL, or DO NOTHING recommendation.

Coin Information:
• Name: {name}
• Symbol: {symbol}
• Source: {source_type}

Market Data (USD):
• Current Price: ${price:,.8f}
• 24h Open: ${open:,.8f}
• 24h High: ${high:,.8f}
• 24h Low: ${low:,.8f}
• 24h Volume: ${volume:,.2f}
• Market Cap Rank: #{market_cap_rank}
• 24h Change: {change:,.2f}%
• 7d Change: {change_7d:,.2f}%
• 30d Change: {change_30d:,.2f}%

Community Data:
{community_data}

IMPORTANT: Start your response with one of these recommendations:
RECOMMENDATION: BUY
RECOMMENDATION: SELL
RECOMMENDATION: DO NOTHING

Then provide your detailed analysis.
"""

"""
Main Agent Code Below
=================================
"""

import os
import requests
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import openai
from typing import Dict, List
import time
from termcolor import colored, cprint
import random
import src.config as config

# Load environment variables
load_dotenv()

# Model override settings
# Set to "0" to use config.py's AI_MODEL setting
# Available models:
# - "deepseek-chat" (DeepSeek's V3 model - fast & efficient)
# - "deepseek-reasoner" (DeepSeek's R1 reasoning model)
# - "0" (Use config.py's AI_MODEL setting)
MODEL_OVERRIDE = "deepseek-r1:1.5b"  # Set to "0" to disable override

# DeepSeek API settings
DEEPSEEK_BASE_URL = "http://localhost:11434/v1"  # Base URL for Ollama DeepSeek API

# 🤖 Agent Model Selection
AI_MODEL = MODEL_OVERRIDE if MODEL_OVERRIDE != "0" else config.AI_MODEL

# Configuration
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
BASE_URL = "https://api.coingecko.com/api/v3"
RESULTS_DIR = Path("moondev/src/data/coingecko_results")
DELAY_BETWEEN_REQUESTS = 1  # Seconds between API calls

# Output files
TOP_GAINERS_LOSERS_FILE = RESULTS_DIR / "top_gainers_losers.csv"
NEW_COINS_FILE = RESULTS_DIR / "new_coins.csv"
AI_PICKS_FILE = RESULTS_DIR / "ai_picks.csv"
AI_BUYS_FILE = RESULTS_DIR / "ai_buys.csv"  # New file for buy signals

# Create results directory
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Fun emoji sets for different actions
SPINNER_EMOJIS = ["🌍", "🌎", "🌏"]  # Earth spinning
MOON_PHASES = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]  # Moon phases
ROCKET_SEQUENCE = ["🚀", "💫", "✨", "💫", "🌟"]  # Rocket launch
ERROR_EMOJIS = ["💥", "🚨", "⚠️", "❌", "🔥"]  # Error indicators
SUCCESS_EMOJIS = ["✨", "🎯", "🎨", "🎪", "🎭", "🎪"]  # Success indicators


def print_spinner(
    message: str, emoji_set: List[str], color: str = "white", bg_color: str = "on_blue"
):
    """Print a spinning emoji animation with message"""
    for emoji in emoji_set:
        print(f"\r{emoji} {colored(message, color, bg_color)}", end="", flush=True)
        time.sleep(0.2)
    print()  # New line after animation


def print_fancy(
    message: str,
    color: str = "white",
    bg_color: str = "on_blue",
    emojis: List[str] = None,
):
    """Print a message with random emojis from set"""
    if emojis:
        emoji = random.choice(emojis)
        cprint(f"{emoji} {message} {emoji}", color, bg_color)
    else:
        cprint(message, color, bg_color)


class NewOrTopAgent:
    """Agent for analyzing new and top performing coins"""

    def __init__(self):
        self.headers = {
            "x-cg-demo-api-key": COINGECKO_API_KEY,
            "Content-Type": "application/json",
        }

        # Initialize AI client based on model
        if "deepseek" in AI_MODEL.lower():
            deepseek_key = "ollama"  # os.getenv("DEEPSEEK_KEY")
            if deepseek_key:
                self.ai_client = openai.OpenAI(
                    api_key=deepseek_key, base_url=DEEPSEEK_BASE_URL
                )
                print(f"🚀 Using DeepSeek model: {AI_MODEL}")
            else:
                raise ValueError("🚨 DEEPSEEK_KEY not found in environment variables!")
        else:
            self.ai_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
            print(f"🤖 Using Claude model: {AI_MODEL}")

        print_fancy(
            "🌙 Moon Dev's New & Top Coins Agent Initialized! 🌟",
            "white",
            "on_magenta",
            SUCCESS_EMOJIS,
        )

    def get_top_gainers(self) -> pd.DataFrame:
        """Get trending coins instead of top gainers (free endpoint)"""
        try:
            print_spinner(
                "🚀 Fetching trending coins...", ROCKET_SEQUENCE, "cyan", "on_blue"
            )
            response = requests.get(f"{BASE_URL}/search/trending", headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                coins = pd.DataFrame([item["item"] for item in data["coins"]])

                if not coins.empty:
                    coins["type"] = "trending"
                    coins["timestamp"] = datetime.now().isoformat()
                    coins["coingecko_url"] = coins["id"].apply(
                        lambda x: f"https://www.coingecko.com/en/coins/{x}"
                    )
                    print(coins)
                    coins.to_csv(TOP_GAINERS_LOSERS_FILE, index=False)

                    print_fancy("\n🚀 Trending Coins Found:", "white", "on_green")
                    for _, coin in coins.iterrows():
                        price_str = (
                            f"#{coin['market_cap_rank']}"
                            if "market_cap_rank" in coin
                            else "N/A"
                        )
                        print_fancy(
                            f"{coin['name']} ({coin['symbol'].upper()}) Rank: {price_str}",
                            "green",
                            "on_grey",
                            ["💰", "🚀", "📈"],
                        )

                    return coins
                else:
                    print_fancy(
                        "No trending coins found in this cycle", "yellow", "on_grey"
                    )
                    return pd.DataFrame()

            else:
                print_fancy(
                    f"Error fetching trending coins: {response.text}",
                    "white",
                    "on_red",
                    ERROR_EMOJIS,
                )
                return pd.DataFrame()

        except Exception as e:
            print_fancy(f"Error: {str(e)}", "white", "on_red", ERROR_EMOJIS)
            return pd.DataFrame()

    def get_new_coins(self) -> pd.DataFrame:
        """Get latest coins using the free simple markets endpoint"""
        try:
            print_spinner("Scanning for new coins...", MOON_PHASES, "yellow", "on_blue")
            response = requests.get(
                f"{BASE_URL}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "volume_desc",  # High volume coins
                    "per_page": 250,
                    "page": 1,
                    "sparkline": False,
                },
            )

            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                df["timestamp"] = datetime.now().isoformat()
                df["coingecko_url"] = df["id"].apply(
                    lambda x: f"https://www.coingecko.com/en/coins/{x}"
                )
                df.to_csv(NEW_COINS_FILE, index=False)

                print_fancy(
                    f"🎯 Found {len(df)} active tokens!",
                    "cyan",
                    "on_grey",
                    SUCCESS_EMOJIS,
                )
                return df

            else:
                print_fancy(
                    f"Error fetching coins: {response.text}",
                    "white",
                    "on_red",
                    ERROR_EMOJIS,
                )
                return pd.DataFrame()

        except Exception as e:
            print_fancy(f"Error: {str(e)}", "white", "on_red", ERROR_EMOJIS)
            return pd.DataFrame()

    def get_coin_data(self, coin_id: str) -> Dict:
        """Get detailed data for a coin"""
        try:
            print_spinner(
                f"Analyzing {coin_id}...", ROCKET_SEQUENCE, "yellow", "on_blue"
            )

            # Get OHLCV data first
            ohlcv_response = requests.get(
                f"{BASE_URL}/coins/{coin_id}/ohlc",
                headers=self.headers,
                params={"vs_currency": "usd", "days": "1"},
            )

            # Get main coin data
            response = requests.get(
                f"{BASE_URL}/coins/{coin_id}",
                headers=self.headers,
                params={
                    "localization": False,
                    "tickers": True,
                    "market_data": True,
                    "community_data": True,
                    "developer_data": False,  # No longer needed
                },
            )

            if response.status_code == 200 and ohlcv_response.status_code == 200:
                coin_data = response.json()
                ohlcv_data = ohlcv_response.json()

                # Convert OHLCV to DataFrame without printing
                if ohlcv_data and len(ohlcv_data) > 0:
                    ohlcv_df = pd.DataFrame(
                        ohlcv_data,
                        columns=["timestamp", "open", "high", "low", "close"],
                    )
                    latest_ohlcv = ohlcv_df.iloc[-1]

                    # Create market data DataFrame
                    market_data = {
                        "price": coin_data.get("market_data", {})
                        .get("current_price", {})
                        .get("usd", 0),
                        "open": latest_ohlcv["open"],
                        "high": latest_ohlcv["high"],
                        "low": latest_ohlcv["low"],
                        "close": latest_ohlcv["close"],
                        "volume": coin_data.get("market_data", {})
                        .get("total_volume", {})
                        .get("usd", 0),
                        "market_cap_rank": coin_data.get("market_cap_rank", "N/A"),
                        "change_24h": coin_data.get("market_data", {}).get(
                            "price_change_percentage_24h", 0
                        ),
                        "change_7d": coin_data.get("market_data", {}).get(
                            "price_change_percentage_7d", 0
                        ),
                        "change_30d": coin_data.get("market_data", {}).get(
                            "price_change_percentage_30d", 0
                        ),
                    }

                    market_df = pd.DataFrame([market_data])
                    coin_data["market_data_df"] = market_df
                    coin_data["ohlcv_df"] = ohlcv_df

                print_fancy(
                    f"✨ Intel gathered on {coin_id}!",
                    "green",
                    "on_grey",
                    SUCCESS_EMOJIS,
                )
                return coin_data
            else:
                print_fancy(
                    f"Error fetching coin data: {response.text}",
                    "white",
                    "on_red",
                    ERROR_EMOJIS,
                )
                return {}

        except Exception as e:
            print_fancy(f"Error: {str(e)}", "white", "on_red", ERROR_EMOJIS)
            return {}

    def analyze_coin(self, coin_data: Dict, source_type: str) -> str:
        """Analyze a coin using AI"""
        try:
            name = coin_data.get("name")
            symbol = coin_data.get("symbol", "").upper()

            # Clear visual break before new analysis
            print("\n" + "=" * 80)
            print_fancy(
                "🤖 STARTING NEW AI ANALYSIS 🤖", "white", "on_magenta", ROCKET_SEQUENCE
            )
            print("=" * 80)

            # Get current price with fallback values
            current_price = (
                coin_data.get("market_data", {}).get("current_price", {}).get("usd", 0)
            )

            # Format price string with fallback
            price_str = (
                f"${current_price:,.8f}" if current_price else "Price unavailable"
            )

            # Show which coin we're analyzing
            print_fancy(f"Token: {name} ({symbol})", "cyan", "on_grey")
            print_fancy(f"Current Price: {price_str}", "cyan", "on_grey")
            print("=" * 80 + "\n")

            # Extract market data with fallbacks
            market_data = {
                "price": coin_data.get("market_data", {})
                .get("current_price", {})
                .get("usd")
                or coin_data.get("current_price", {}).get("usd")
                or current_price,
                "open": coin_data.get("market_data", {})
                .get("price_change_24h_in_currency", {})
                .get("usd", 0),
                "high": coin_data.get("market_data", {}).get("high_24h", {}).get("usd")
                or coin_data.get("high_24h", {}).get("usd", 0),
                "low": coin_data.get("market_data", {}).get("low_24h", {}).get("usd")
                or coin_data.get("low_24h", {}).get("usd", 0),
                "volume": coin_data.get("market_data", {})
                .get("total_volume", {})
                .get("usd")
                or coin_data.get("total_volume", {}).get("usd", 0),
                "market_cap_rank": coin_data.get("market_cap_rank", "N/A"),
                "change_24h": coin_data.get("market_data", {}).get(
                    "price_change_percentage_24h"
                )
                or coin_data.get("price_change_percentage_24h", 0),
                "change_7d": coin_data.get("market_data", {}).get(
                    "price_change_percentage_7d", 0
                ),
                "change_30d": coin_data.get("market_data", {}).get(
                    "price_change_percentage_30d", 0
                ),
            }

            # Format prompt with market data
            prompt = AI_PROMPT.format(
                name=name,
                symbol=symbol,
                source_type=source_type,
                price=market_data["price"],
                open=market_data["open"],
                high=market_data["high"],
                low=market_data["low"],
                volume=market_data["volume"],
                market_cap_rank=market_data["market_cap_rank"],
                change=market_data["change_24h"],
                change_7d=market_data["change_7d"],
                change_30d=market_data["change_30d"],
                community_data=json.dumps(
                    coin_data.get("community_data", {}), indent=2
                ),
            )

            print_fancy(
                "🧠 AI Agent Processing...", "yellow", "on_blue", SPINNER_EMOJIS
            )

            # Get AI response based on model
            if "deepseek" in AI_MODEL.lower():
                response = self.ai_client.chat.completions.create(
                    model=AI_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a cryptocurrency analyst.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )
                analysis = response.choices[0].message.content
            else:
                response = self.ai_client.messages.create(
                    model=AI_MODEL,
                    max_tokens=500,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}],
                )
                analysis = response.content[0].text

            # Extract and display recommendation
            recommendation = self.extract_recommendation(analysis)
            change_str = f"{market_data['change_24h']:+.2f}%"

            # Show recommendation with dramatic spacing
            print("\n" + "🎯 " * 20)
            if recommendation == "BUY":
                print_fancy(
                    f"RECOMMENDATION FOR {name} ({symbol}):",
                    "white",
                    "on_green",
                    ["💰", "🚀"],
                )
                print_fancy(
                    f"BUY @ {price_str} ({change_str})",
                    "white",
                    "on_green",
                    ["💰", "🚀", "📈"],
                )
            elif recommendation == "SELL":
                print_fancy(
                    f"RECOMMENDATION FOR {name} ({symbol}):",
                    "white",
                    "on_red",
                    ["💸", "📉"],
                )
                print_fancy(
                    f"SELL @ {price_str} ({change_str})",
                    "white",
                    "on_red",
                    ["💸", "🔻", "📉"],
                )
            else:
                print_fancy(
                    f"RECOMMENDATION FOR {name} ({symbol}):",
                    "white",
                    "on_blue",
                    ["🎯", "⏳"],
                )
                print_fancy(
                    f"DO NOTHING @ {price_str} ({change_str})",
                    "white",
                    "on_blue",
                    ["🎯", "⏳", "🔄"],
                )
            print("🎯 " * 20 + "\n")

            # End of analysis marker
            print("=" * 80)
            print_fancy("AI ANALYSIS COMPLETE", "white", "on_magenta", SUCCESS_EMOJIS)
            print("=" * 80 + "\n")

            return analysis

        except Exception as e:
            print_fancy(
                f"Error in AI analysis: {str(e)}", "white", "on_red", ERROR_EMOJIS
            )
            return "Error in analysis"

    def extract_recommendation(self, analysis: str) -> str:
        """Extract BUY/SELL/DO NOTHING from analysis"""
        if "RECOMMENDATION: BUY" in analysis:
            return "BUY"
        elif "RECOMMENDATION: SELL" in analysis:
            return "SELL"
        return "DO NOTHING"

    def save_analysis(self, result: Dict):
        """Save a single analysis result to CSV"""
        # Ensure all required fields exist with default values
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'coin_id': result['coin_id'],  # Direct dictionary access
            'name': result['name'],
            'symbol': result['symbol'],
            'source': result['source'],
            'price_usd': float(result['price_usd']),  # Direct access and ensure float
            'volume_24h': float(result['volume_24h']),
            'price_change_24h': float(result['price_change_24h']),
            'recommendation': result['recommendation'],
            'coingecko_url': result['coingecko_url']
        }

        df = pd.DataFrame([analysis_data])
        
        # Save to main picks file
        if os.path.exists(AI_PICKS_FILE):
            df.to_csv(AI_PICKS_FILE, mode='a', header=False, index=False)
        else:
            df.to_csv(AI_PICKS_FILE, index=False)
        
        # If it's a BUY recommendation, also save to buys file
        if analysis_data['recommendation'] == "BUY":
            if os.path.exists(AI_BUYS_FILE):
                df.to_csv(AI_BUYS_FILE, mode='a', header=False, index=False)
            else:
                df.to_csv(AI_BUYS_FILE, index=False)
            print_fancy(f"💰 Added {analysis_data['name']} to AI Buys!", 'white', 'on_green', ['💰', '🚀', '📈'])
        else:
            print_fancy(f"💾 Saved analysis for {analysis_data['name']}", 'white', 'on_green', SUCCESS_EMOJIS)


    def run_analysis(self):
        """Run complete analysis cycle"""
        print_spinner(
            "🚀 Initiating Moon Dev Analysis Sequence...",
            ROCKET_SEQUENCE,
            "white",
            "on_magenta",
        )

        # Get only top gainers and new coins
        top_gainers_df = self.get_top_gainers()
        new_coins_df = self.get_new_coins()

        total_analyzed = 0

        # Analyze top gainers
        if not top_gainers_df.empty:
            for _, coin in top_gainers_df.iterrows():
                coin_data = self.get_coin_data(coin["id"])
                if coin_data:
                    analysis = self.analyze_coin(coin_data, "Top gainer")
                    recommendation = self.extract_recommendation(analysis)

                    result = {
                        "timestamp": datetime.now().isoformat(),
                        "coin_id": coin_data.get("id", coin["id"]),  # Use coin_data id with fallback to coin id
                        "name": coin_data.get("name", coin["name"]),
                        "symbol": coin_data.get("symbol", coin["symbol"]),
                        "source": "Top gainer",
                        "price_usd": float(coin_data.get("market_data", {}).get("current_price", {}).get("usd", 0)),
                        "volume_24h": float(coin_data.get("market_data", {}).get("total_volume", {}).get("usd", 0)),
                        "price_change_24h": float(coin_data.get("market_data", {}).get("price_change_percentage_24h", 0)),
                        "recommendation": recommendation,
                        "coingecko_url": f"https://www.coingecko.com/en/coins/{coin_data.get('id', coin['id'])}"
                    }

                    # Save each analysis immediately
                    self.save_analysis(result)
                    total_analyzed += 1

                time.sleep(DELAY_BETWEEN_REQUESTS)

        # Analyze new coins
        if not new_coins_df.empty:
            for _, coin in new_coins_df.iterrows():
                coin_data = self.get_coin_data(coin["id"])
                if coin_data:
                    analysis = self.analyze_coin(coin_data, "Recently Added")
                    recommendation = self.extract_recommendation(analysis)

                    result = {
                        "timestamp": datetime.now().isoformat(),
                        "coin_id": coin_data.get("id", coin["id"]),
                        "name": coin_data.get("name", coin["name"]),
                        "symbol": coin_data.get("symbol", coin["symbol"]),
                        "source": "Top gainer",
                        "price_usd": float(coin_data["market_data_df"]["price"].iloc[0]) if "market_data_df" in coin_data else float(coin_data.get("market_data", {}).get("current_price", {}).get("usd", 0)),
                        "volume_24h": float(coin_data["market_data_df"]["volume"].iloc[0]) if "market_data_df" in coin_data else float(coin_data.get("market_data", {}).get("total_volume", {}).get("usd", 0)),
                        "price_change_24h": float(coin_data["market_data_df"]["change_24h"].iloc[0]) if "market_data_df" in coin_data else float(coin_data.get("market_data", {}).get("price_change_percentage_24h", 0)),
                        "recommendation": recommendation,
                        "coingecko_url": f"https://www.coingecko.com/en/coins/{coin_data.get('id', coin['id'])}"
                    }

                    # Save each analysis immediately
                    self.save_analysis(result)
                    total_analyzed += 1

                time.sleep(DELAY_BETWEEN_REQUESTS)

        # Print final summary
        if total_analyzed > 0:
            print_fancy("\n🎮 ANALYSIS COMPLETE 🎮", "white", "on_green")
            print_fancy("=" * 50, "blue", "on_white")

            # Read the full file to get summary
            results_df = pd.read_csv(AI_PICKS_FILE)
            summary = results_df["recommendation"].value_counts()

            print_fancy(f"BUY: {summary.get('BUY', 0)} 💰", "green", "on_grey")
            print_fancy(f"SELL: {summary.get('SELL', 0)} 📉", "red", "on_grey")
            print_fancy(
                f"DO NOTHING: {summary.get('DO NOTHING', 0)} 🎯", "yellow", "on_grey"
            )
            print_fancy("=" * 50, "blue", "on_white")


def main():
    """Main function to run the agent"""
    print_fancy(
        "\n🌙 Moon Dev's Cosmic Token Analysis Starting! 🌟",
        "white",
        "on_magenta",
        SUCCESS_EMOJIS,
    )
    agent = NewOrTopAgent()

    try:
        while True:
            agent.run_analysis()
            for emoji in MOON_PHASES:
                print_fancy(
                    f"{emoji} Waiting for next analysis cycle...", "cyan", "on_blue"
                )
                time.sleep(450)  # 450 * 8 = 3600 (1 hour)

    except KeyboardInterrupt:
        print_fancy(
            "\n👋 Agent stopped by user - Moon Dev out! 🌙", "white", "on_magenta"
        )
    except Exception as e:
        print_fancy(f"\nError: {str(e)}", "white", "on_red", ERROR_EMOJIS)


if __name__ == "__main__":
    main()
