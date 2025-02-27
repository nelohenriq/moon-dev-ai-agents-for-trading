"""
🌙 Moon Dev's RBI Agent (Research-Backtest-Implement)
Built with love by Moon Dev 🚀

Required Setup:
1. Create folder structure:
   src/
   ├── data/
   │   └── rbi/
   │       ├── research/         # Strategy research outputs
   │       ├── backtests/        # Initial backtest code
   │       ├── backtests_final/  # Debugged backtest code
   │       ├── BTC-USD-15m.csv  # Price data for backtesting
   │       └── ideas.txt        # Trading ideas to process

2. Environment Variables:
   - DEEPSEEK_KEY: Your DeepSeek API key

3. Create ideas.txt:
   - One trading idea per line
   - Can be YouTube URLs, PDF links, or text descriptions
   - Lines starting with # are ignored

This agent automates the RBI process:
1. Research: Analyzes trading strategies from various sources
2. Backtest: Creates backtests for promising strategies
3. Debug: Fixes technical issues in generated backtests

Remember: Past performance doesn't guarantee future results!
"""

# DeepSeek Model Selection per Agent
# Set to "0" to use config.py's AI_MODEL setting
# Options for each: "deepseek-chat" (faster) or "deepseek-reasoner" (more analytical)   # Careful code analysis
RESEARCH_MODEL = "deepseek-r1-distill-llama-70b"  # use ollama locally "deepseek-r1:1.5b" # use groq model deepseek-r1-distill-llama-70b # Analyzes strategies thoroughly
BACKTEST_MODEL = "deepseek-r1-distill-llama-70b"  # use ollama locally "deepseek-r1:1.5b" # use groq model deepseek-r1-distill-llama-70b # Creative in implementing strategies
DEBUG_MODEL = "deepseek-r1-distill-llama-70b"  # use ollama locally "qwen2.5-coder:3b"    # use groq model deepseek-r1-distill-llama-70b # Careful code analysis

# Agent Prompts

RESEARCH_PROMPT = """
You are Moon Dev's Solana Memecoin Research AI 🌙

Your task is to analyze YouTube transcripts where traders discuss finding early Solana memecoin opportunities. Extract key insights and structure them into actionable research.

IMPORTANT NAMING RULES:
1. Create a UNIQUE TWO-WORD NAME that summarizes the key approach in the transcript.
2. The first word should describe the main method (e.g., Whale, Social, Volume, Insider, Bot, Trend, Sniper).
3. The second word should describe the specific technique (e.g., Tracking, Signals, Alerts, Patterns, Analysis).
4. Ensure the name is SPECIFIC to the transcript's insights.

Examples:
- "WhaleTracking" for methods that monitor big wallets entering new tokens.
- "SocialHype" for tracking viral trends on Twitter/Telegram.
- "BotAlerts" for detecting memecoins launched via sniper bots.

BAD names to avoid:
- "CryptoResearch" (too generic)
- "SolanaStrategy" (too vague)
- "TokenFinder" (not specific enough)

Output format must start with:
STRATEGY_NAME: [Your unique two-word name]

Then analyze the transcript and extract key insights:
1. **How do they find early Solana memecoins?** (Methods & tools mentioned)
2. **What are the key signals of a promising token?** (Liquidity, wallets, socials, market cap, etc.)
3. **What are the risks to watch out for?** (Rug pulls, bot activity, honeypots)
4. **Any specific websites, tools, or indicators used?**

STRATEGY_DETAILS:
[Your structured insights from the transcript]

Remember: Your analysis should be practical and actionable! 🚀"""

BACKTEST_PROMPT = """
You are Moon Dev's Backtest AI 🌙
Instead of backtesting trading strategies, you will now evaluate and simulate memecoin discovery methods based on YouTube transcripts.

Your goal is to test the effectiveness of different approaches using historical token launch data.

### KEY TASKS:
1. **Simulate different discovery methods** (e.g., tracking wallets, Telegram mentions, Twitter trends, etc.)
2. **Test these methods using past Solana memecoin launches** (e.g., identifying tokens early and checking their later performance)
3. **Evaluate success rates** (e.g., how many identified tokens performed well vs. rugged)
4. **Provide detailed results with data-driven insights**

### DATA HANDLING:
- Use past Solana token launches from sources like DEX Screener, SolScan, and Helius RPC.
- Ensure proper data cleaning (e.g., remove duplicates, check timestamps, align with discovery methods).
- Track wallet interactions and market data for historical validation.

### OUTPUT FORMAT:
1. Print the effectiveness of each method with statistics.
2. Identify the best-performing discovery strategies.
3. Highlight any flaws or risks in the methods tested.

Remember: Focus on practical analysis that helps users refine their Solana memecoin research process! 🚀"""

DEBUG_PROMPT = """
You are Moon Dev's Debug AI 🌙
Fix technical issues in the memecoin discovery backtest code WITHOUT changing the research logic.

Focus on:
1. Syntax errors (like incorrect string formatting)
2. API calls (Helius RPC, DEX Screener, etc.)
3. Data parsing (correct Solana token data handling)
4. Variable scoping and naming
5. Print statement formatting

DO NOT change:
1. Discovery logic
2. Data sources
3. Statistical evaluation methods

Return the complete fixed code with debug messages where necessary. 🚀"""

PACKAGE_PROMPT = """
You are Moon Dev's Packaging AI 🌙
Ensure that the memecoin discovery backtest code follows best practices and does not rely on unnecessary external libraries.

STRICT RULES:
1. **NO backtesting.py or trading-related libraries** (this is for memecoin discovery, not trading bots).
2. **Use web scraping or API calls for real-time data** (e.g., Twitter, Telegram, DEX Screener, SolScan, Helius RPC).
3. **Ensure efficient data handling** (use pandas or numpy for processing large datasets).
4. **Replace any redundant imports with optimized alternatives**.

Example fixes:
- ❌ "from backtesting.lib import *"
- ✅ Use pandas or numpy for data processing instead

Return the complete optimized code with proper Moon Dev-themed debug prints! 🌙 ✨"""


def get_model_id(model):
    """Get DR/DC identifier based on model type"""
    if "7b" in model:
        return "DR"  # Deep Reasoner for 7B models
    elif "1.5b" in model:
        return "DC"  # Deep Coder for 1.5B models
    elif "coder" in model.lower():
        return "CD"  # Deep Coder for coder models
    else:
        return "DR"  # Default to DR for other cases


import os
import time
import re
from datetime import datetime
import requests
from io import BytesIO
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from pathlib import Path
from termcolor import cprint
import threading
import itertools
import pandas as pd
import sys
import re
from langsmith import traceable
from dotenv import load_dotenv
import csv

load_dotenv()

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"] = "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"
os.environ["LANGSMITH_PROJECT"] = "pr-charming-personnel-66"

# DeepSeek Configuration
DEEPSEEK_BASE_URL = "http://localhost:11434/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
HELIUS_RPC_URL = (
    "https://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"
)
DEX_SCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"


# Update data directory paths
PROJECT_ROOT = Path(__file__).parent.parent  # Points to src/
DATA_DIR = PROJECT_ROOT / "data/memecoins"
RESEARCH_DIR = DATA_DIR / "research"
BACKTEST_DIR = DATA_DIR / "backtests"
PACKAGE_DIR = DATA_DIR / "backtests_package"
FINAL_BACKTEST_DIR = DATA_DIR / "backtests_final"
CHARTS_DIR = DATA_DIR / "charts"  # New directory for HTML charts

TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_LAUNCH_CSV = PROJECT_ROOT / "token_launches.csv"

print(f"📂 Using RBI data directory: {DATA_DIR}")
print(f"📂 Research directory: {RESEARCH_DIR}")
print(f"📂 Backtest directory: {BACKTEST_DIR}")
print(f"📂 Package directory: {PACKAGE_DIR}")
print(f"📂 Final backtest directory: {FINAL_BACKTEST_DIR}")
print(f"📈 Charts directory: {CHARTS_DIR}")


@traceable
def init_deepseek_client():
    """Initialize DeepSeek client with proper error handling"""
    try:
        print("🔑 Initializing DeepSeek client...")
        print("🌟 Moon Dev's Sniper Agent is connecting to DeepSeek...")

        groq_api_key = os.getenv("GROQ_API_KEY")

        client = openai.OpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)

        print("✅ DeepSeek client initialized successfully!")
        print(
            "🚀 Moon Dev's Sniper Agent ready to analyze Solana memecoin opportunities!"
        )
        return client
    except Exception as e:
        print(f"❌ Error initializing DeepSeek client: {str(e)}")
        print("💡 Check if your GROQ_API_KEY is valid and properly set")
        return None


@traceable
def chat_with_deepseek(system_prompt, user_content, model):
    """Chat with DeepSeek API using specified model"""
    print(f"\n🤖 Starting chat with DeepSeek using {model}...")
    print("🌟 Moon Dev's Sniper Agent is analyzing the transcript...")

    client = init_deepseek_client()
    if not client:
        print("❌ Failed to initialize DeepSeek client")
        return None

    try:
        print("📤 Sending request to DeepSeek API...")
        print(f"🎯 Model: {RESEARCH_MODEL}")
        print(
            "🔄 Please wait while Moon Dev's Sniper Agent extracts insights from the transcript..."
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
        )

        if not response or not response.choices:
            print("❌ Empty response from DeepSeek API")
            return None

        print("📥 Received response from DeepSeek API!")
        print(
            f"✨ Extracted insights length: {len(response.choices[0].message.content)} characters"
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error in DeepSeek chat: {str(e)}")
        print("💡 This could be due to API rate limits or invalid requests")
        print(f"🔍 Error details: {str(e)}")
        return None


@traceable
def extract_transcript(video_id):
    """Extracts transcript from a YouTube video given its URL."""
    if not video_id:
        print("❌ Invalid YouTube VIDEO_ID!")
        return None

    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id=video_id, languages=["en"]
        )
        cprint("📺 Successfully fetched YouTube transcript!", "green")
        text = " ".join([entry["text"] for entry in transcript])
        return text
    except Exception as e:
        print(f"⚠️ Failed to extract transcript: {e}")
        return None


def animate_progress(agent_name, stop_event):
    """Fun animation while agent is thinking"""
    spinners = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
    messages = [
        "brewing coffee ☕️",
        "studying charts 📊",
        "checking signals 📡",
        "doing math 🔢",
        "reading docs 📚",
        "analyzing data 🔍",
        "making magic ✨",
        "trading secrets 🤫",
        "Moon Dev approved 🌙",
        "to the moon! 🚀",
    ]

    spinner = itertools.cycle(spinners)
    message = itertools.cycle(messages)

    while not stop_event.is_set():
        sys.stdout.write("\033[K")  # Clear the current line
        sys.stdout.write(f"\r{next(spinner)} {agent_name} is {next(message)}...")
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write("\033[K")  # Clear the line when done
    sys.stdout.write("\r")
    sys.stdout.flush()


def run_with_animation(func, agent_name, *args, **kwargs):
    """Run a function with a fun loading animation"""
    stop_animation = threading.Event()
    animation_thread = threading.Thread(
        target=animate_progress, args=(agent_name, stop_animation)
    )

    try:
        animation_thread.start()
        result = func(*args, **kwargs)
        return result
    finally:
        stop_animation.set()
        animation_thread.join()


def extract_strategy_name_and_text(insights):
    """Extracts the strategy name and strategy insights from the response."""
    strategy_name = None
    strategy = insights.strip()

    # Search for the strategy name using regex
    match = re.search(r"\*\*🔍 Strategy Name\*\*:\s*(.+)", insights)
    if match:
        strategy_name = match.group(1).strip()  # Extract the strategy name

    # Remove the "Strategy Name" line from the insights
    strategy = re.sub(
        r"\*\*🔍 Strategy Name\*\*:\s*.+\n?", "", insights, count=1
    ).strip()

    return strategy_name, strategy


@traceable
def process_transcript(transcript_text):
    """Process a YouTube transcript to extract Solana memecoin insights"""
    print("\n📜 Processing YouTube transcript for Solana memecoin opportunities...")

    system_prompt = """
    You are Moon Dev's Sniper AI 🌙

    Your goal is to analyze this YouTube transcript and extract actionable insights for finding Solana memecoin opportunities.
    
    Please follow these instructions:

    1. **Strategy Name**: Provide a concise name for the trading strategy based on the transcript.
    2. **Strategy Insights**: Summarize the main strategy discussed in the video in a clear and actionable way.
    3. **Indicators & Tools**: List any specific indicators, tools, or platforms mentioned in the transcript.
    4. **Entry Criteria**: Summarize how the speaker decides which memecoins to enter.
    5. **Risk Management**: Describe any risk management strategies mentioned.
    6. **Red Flags**: Identify any red flags or warning signs to avoid bad projects.
    7. **Social & On-Chain Signals**: List any social media, wallet tracking, or on-chain tools referenced.

    Format your output like this:

    **🔍 Strategy Name**: [Provide a name for the strategy]  
    **🔍 Strategy Insights**: [Summary of main strategy]  
    **📊 Indicators & Tools**: [List of any mentioned tools]  
    **🚀 Entry Criteria**: [How they decide which memecoins to enter]  
    **⚠️ Risk Management**: [Any mentioned safety measures]  
    **🛑 Red Flags**: [Warning signs to avoid bad projects]  
    **📢 Social & On-Chain Signals**: [Mentioned sources for information]  

    Ensure that the **Strategy Name** is clearly formatted as "**🔍 Strategy Name**: [Your Strategy Name]".
    """

    insights = chat_with_deepseek(
        RESEARCH_PROMPT, transcript_text, model=RESEARCH_MODEL
    )

    if insights:
        print("\n✅ Extracted Memecoin Research Insights:")
        print(insights)

        # Extract strategy name and strategy text
        strategy_name, strategy = extract_strategy_name_and_text(insights)

        if not strategy_name:
            print("⚠️ Warning: Strategy name could not be extracted. Using fallback.")
            strategy_name = "Unnamed_Strategy"

        # Sanitize strategy name for use as a filename
        sanitized_strategy_name = re.sub(r'[<>:"/\\|?*]', "_", strategy_name)

        # Save strategy to file with sanitized strategy name
        strategy_file = RESEARCH_DIR / f"strategy_DC_{sanitized_strategy_name}.txt"

        with open(strategy_file, "w") as f:
            f.write(strategy)

        print(f"\n📝 Strategy saved to {strategy_file}")

        return strategy, sanitized_strategy_name
    else:
        print("\n❌ Failed to extract insights from transcript.")
        return None, None


def clean_token_data(df):
    """Cleans token launch data before analysis."""
    df = df.dropna()  # Remove empty rows
    df["created_at"] = pd.to_datetime(df["created_at"], unit="s")  # Convert timestamps
    df = df.sort_values(by="created_at", ascending=False)  # Sort by newest launches

    return df


@traceable
def get_new_token_mints():
    """Fetch newly minted Solana SPL tokens using Helius RPC, excluding non-token program transactions."""

    # Initialize a set to keep track of seen transactions
    seen_transactions = set()

    url = HELIUS_RPC_URL
    current_time = int(time.time())
    one_hour_ago = current_time - 3600  # One hour ago in Unix timestamp

    # Define the list of program IDs to be excluded
    excluded_program_ids = [
        "So11111111111111111111111111111111111111112",  # Solana System Program ID
        "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",  # Example non-token program
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # Another example non-token program
        "11111111111111111111111111111111",  # Example non-token program
        # Add other program IDs you want to exclude
    ]

    response = requests.post(
        url,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                TOKEN_PROGRAM_ID,  # Track transactions for Token Program
                {"limit": 20},  # Fetch latest 20 transactions
            ],
        },
    )

    if response.status_code != 200:
        print(f"❌ Error fetching transactions: {response.status_code}")
        return []

    transactions = response.json().get("result", [])
    new_tokens = []

    for tx in transactions:
        sig = tx["signature"]

        if tx["blockTime"] > one_hour_ago:
            break  # Stop processing if we've reached transactions older than one hour

        if sig in seen_transactions:  # Avoid duplicate processing
            continue

        seen_transactions.add(sig)  # Mark transaction as processed

        # Fetch transaction details
        tx_response = requests.post(
            url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    sig,
                    {"maxSupportedTransactionVersion": 0},
                ],  # Get parsed transaction details
            },
        )

        if tx_response.status_code != 200:
            print(f"⚠️ Error fetching transaction {sig}: {tx_response.status_code}")
            continue

        tx_data = tx_response.json().get("result", {})

        # Check if the transaction involves any excluded program IDs
        if "meta" in tx_data and tx_data["meta"].get("err") is None:
            if "postTokenBalances" in tx_data["meta"]:
                for balance_change in tx_data["meta"]["postTokenBalances"]:
                    mint_address = balance_change["mint"]

                    # Exclude transactions involving unwanted program IDs
                    if any(
                        mint_address == excluded_program_id
                        for excluded_program_id in excluded_program_ids
                    ):
                        continue

                    # Ensure mint address is unique
                    if mint_address not in [t["mint_address"] for t in new_tokens]:
                        new_tokens.append(
                            {
                                "mint_address": mint_address,
                                "created_at": tx.get("blockTime", time.time()),
                            }
                        )

    return new_tokens


@traceable
def track_token_launches():
    """Monitor token launches continuously and pass newly found tokens for analysis."""
    analyzed_tokens = []  # Initialize the list to track analyzed tokens
    analyzed_token_addresses = set()

    while True:
        # Fetch new token mints from the blockchain
        new_tokens = get_new_token_mints()

        # If no new tokens found, continue monitoring
        if not new_tokens:
            print("⏳ No new tokens found, continuing to monitor...")
            time.sleep(10)  # Shorter wait between cycles if no new tokens
            continue

        # Process and analyze the new tokens
        for token in new_tokens:
            print(f"🔍 Analyzing token: {token['mint_address']}")
            token_address = token["mint_address"]

            if token_address in analyzed_token_addresses:
                print(f"⚠️ Token {token_address} already analyzed.")
                continue

            analyzed_token = analyze_token_metrics(token_address)

            if analyzed_token:
                # Store the analyzed token if not already included
                analyzed_token["token_address"] = token_address
                # Add the token address to the set of analyzed tokens
                analyzed_token_addresses.add(token_address)
                # Append the analyzed token to the list
                analyzed_tokens.append(analyzed_token)

        # After all tokens are analyzed, save the data to CSV or any other storage
        print("🚀 Attempting to save tokens to CSV...")
        try:
            save_analyzed_tokens_to_csv(
                analyzed_tokens, PROJECT_ROOT / "data/analyzed_tokens.csv"
            )
            print("✅ Tokens saved successfully.")
        except Exception as e:
            print(f"❌ Error saving tokens to CSV: {e}")

        # After all tokens are analyzed, sleep before starting the next monitoring cycle
        print("✅ Analysis complete for this cycle. Sleeping before the next cycle.")
        time.sleep(60)  # Sleep for 60 seconds (or any duration you choose)


@traceable
def save_analyzed_tokens_to_csv(tokens, file_path):
    """Save analyzed tokens to a CSV file."""
    file_path = Path(file_path)

    # Ensure the directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert a single dictionary to a list if necessary
    if isinstance(tokens, dict):
        tokens = [tokens]

    if not tokens:
        print("⚠️ No tokens to save!")
        return

    # Debugging: Print tokens before writing
    print(f"📁 Saving to: {file_path.resolve()}")

    # Check if file exists
    file_exists = file_path.exists()

    # Flatten token data
    flat_tokens = []
    for token in tokens:
        liquidity = token.get("liquidity", {})
        if not isinstance(liquidity, dict):
            liquidity = {
                "usd": 0,
                "base": 0,
                "quote": 0,
            }  # Handle cases where liquidity is an integer

        token_address = token.get(
            "token_address", "N/A"
        )  # Ensure token address is included

        dex_screener_link = (
            f"https://dexscreener.com/solana/{token_address}"
            if token_address != "N/A"
            else "N/A"
        )

        axiom_trade_link = (
            f"https://axiom.trade/meme/{token_address}"
            if token_address != "N/A"
            else "N/A"
        )

        # Get social links as a comma-separated string, handle missing or empty "url" field
        social_links = (
            ", ".join([s["url"] for s in token.get("social_links", []) if "url" in s])
            if token.get("social_links")
            else "N/A"
        )

        # Flatten token data into a dictionary
        flat_token = {
            "symbol": token.get("symbol", "N/A"),
            "liquidity_usd": liquidity.get("usd", 0),
            "liquidity_base": liquidity.get("base", 0),
            "liquidity_quote": liquidity.get("quote", 0),
            "volume_24h": token.get("volume_24h", 0),
            "holders": token.get("holders", 0),
            "dex": token.get("dex", "Unknown"),
            "token_address": token_address,
            "dex_screener": dex_screener_link,
            "axiom_trade": axiom_trade_link,
            "social_links": ", ".join(
                [
                    s["url"]
                    for s in token.get("social_links", [])
                    if "url" in s and s["url"] and "dexscreener" not in s["url"] and "axiom.trade" not in s["url"]
                ]
            )
            or "N/A",
        }
        flat_tokens.append(flat_token)

    # Field names
    fieldnames = flat_tokens[0].keys()

    try:
        with open(file_path, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerows(flat_tokens)

        print(f"✅ Analyzed tokens saved to {file_path}")
    except Exception as e:
        print(f"❌ Error saving tokens to CSV: {e}")
        raise  # Print full traceback


def format_market_data(market_data):
    """Format the market data (e.g., usd, base, quote)."""
    if isinstance(market_data, dict):
        return f"USD: {market_data.get('usd', 'N/A')}, Base: {market_data.get('base', 'N/A')}, Quote: {market_data.get('quote', 'N/A')}"
    return "N/A"


def format_value(value):
    """Format numeric values."""
    try:
        return f"{float(value):,.2f}" if value is not None else "N/A"
    except ValueError:
        return "N/A"


def format_social_links(socials):
    """Format the social links."""
    if socials:
        formatted_links = [
            f"{social['type'].capitalize()} - {social['url']}" for social in socials
        ]
        return ", ".join(formatted_links)
    return "None"


@traceable
def analyze_token_metrics(token_address):
    """Fetches and analyzes token liquidity, volume, and holders."""
    url = f"{DEX_SCREENER_API}{token_address}"
    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json().get("pairs", [])

            if not data:
                print(f"⚠️ No valid data returned for {token_address}")
                return None

            # You can customize this if you need to analyze multiple pairs.
            pair_data = data[0]  # Default to the first pair (you can adjust this logic)

            # Check for Raydium filter
            dex = pair_data.get("dexId", "Unknown")  # Default to "Unknown" if not found
            if dex.lower() != "raydium":
                print(
                    f"⚠️ Token {token_address} is not a Raydium token, skipping analysis."
                )
                return None

            analysis = {
                "symbol": pair_data.get("baseToken", {}).get("symbol", "N/A"),
                "token_address": token_address,
                "liquidity": pair_data.get("liquidity", 0),  # Default to 0 if not found
                "volume_24h": pair_data.get("volume", {}).get(
                    "h24", 0
                ),  # Default to 0 if not found
                "holders": pair_data.get("holders", 0),  # Default to 0 if not found
                "dex": dex,
                "social_links": pair_data.get("info", {}).get(
                    "socials", []
                ),  # Default to empty list if not found
            }

            # You could add more pairs or different fields here if needed
            return analysis
        else:
            print(
                f"⚠️ Failed to fetch token data for {token_address} - Status code: {response.status_code}"
            )
            return None

    except requests.RequestException as e:
        print(f"❌ Error fetching token data for {token_address}: {e}")
        return None


@traceable
def package_check(backtest_code, strategy_name="UnknownStrategy"):
    """Package Agent: Ensures correct indicator packages are used"""
    cprint("\n📦 Starting Package Agent...\n", "cyan")
    cprint("🔍 Checking for proper indicator imports!", "yellow")

    output = run_with_animation(
        chat_with_deepseek,
        "Package Agent",
        PACKAGE_PROMPT,
        f"Check and fix indicator packages in this code:\n\n{backtest_code}",
        DEBUG_MODEL,
    )

    if output:
        code_match = re.search(r"```python\n(.*?)\n```", output, re.DOTALL)
        if code_match:
            output = code_match.group(1)

        # Save to package directory
        filepath = PACKAGE_DIR / f"{strategy_name}_PKG.py"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(output)
        cprint(
            f"📦 Package Agent optimized the imports! Saved to {filepath} ✨", "green"
        )
        return output
    return None


@traceable
def get_idea_content(idea_url: str) -> str:
    """Extract content from a trading idea URL or text"""
    print("\n📥 Extracting content from idea...")

    try:
        # Ensure the URL is clean
        idea_url = idea_url.strip()
        print(f"Processing URL: {idea_url}")

        if "youtube.com" in idea_url or "youtu.be" in idea_url:
            print(f"Detected YouTube URL: {idea_url}")

            # Use regex to capture the video ID from YouTube URL
            video_id = None
            youtube_regex = r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)"

            match = re.search(youtube_regex, idea_url)

            if match:
                video_id = match.group(1)
                print(f"Extracted video ID: {video_id}")

                print("🎥 Detected YouTube video, fetching transcript...")
                transcript = extract_transcript(video_id)
                print("✅ Successfully extracted YouTube transcript!")

                if transcript:
                    return transcript
                else:
                    raise ValueError("Failed to extract YouTube transcript")
            else:
                raise ValueError(
                    "Invalid YouTube URL format. Could not extract video ID."
                )

        else:
            print("📝 Using raw text input...")
            return f"Text Strategy Content:\n\n{idea_url}"

    except Exception as e:
        print(f"❌ Error extracting content: {str(e)}")
        raise


@traceable
def process_trading_idea(link: str) -> None:
    """Process a trading idea by detecting type and extracting content"""
    print("\n🚀 Moon Dev's RBI Agent Processing New Idea!")
    print("🌟 Let's find some alpha in the chaos!")

    try:
        # Create output directories if they don't exist
        for dir in [
            DATA_DIR,
            RESEARCH_DIR,
            BACKTEST_DIR,
            FINAL_BACKTEST_DIR,
            PACKAGE_DIR,
        ]:
            dir.mkdir(parents=True, exist_ok=True)

        print("💭 Processing raw strategy idea...")

        ## Step 1: Extract content from the idea
        idea_content = get_idea_content(link)
        if not idea_content:
            print("❌ Failed to extract content from idea!")
            return

        print(f"📄 Extracted content length: {len(idea_content)} characters")

        # Phase 1: Research
        print("\n🧪 Phase 1: Research")
        strategy, strategy_name = process_transcript(idea_content)

        if not strategy:
            print("❌ Research phase failed!")
            return

        print(f"🏷️ Strategy Name: {strategy_name}")

        # Save strategy to file with timestamp
        strategy_file = RESEARCH_DIR / f"strategy_{strategy_name}.txt"

        with open(strategy_file, "w") as f:
            f.write(strategy)
        print(f"\n📝 Strategy saved to {strategy_file}")

        # Phase 2: Backtest
        print("\n📈 Phase 2: Backtest")
        mint_address, _ = track_token_launches()

        # Phase 3: Package Check using only the backtest code
        print("\n📦 Phase 3: Package Check")
        package_checked = analyze_token_metrics(mint_address)

        if not package_checked:
            print("❌ Package check failed!")
            return

        # Save package check output
        package_file = PACKAGE_DIR / f"{strategy_name}_PKG.py"
        with open(package_file, "w") as f:
            f.write(package_checked)

        print("\n🎉 Mission Accomplished!")
        print(f"🚀 Strategy '{strategy_name}' is ready to make it rain! 💸")
        print(f"✨ Final backtest saved at: {package_file}")

    except Exception as e:
        print(f"\n❌ Error processing idea: {str(e)}")
        raise


@traceable
def main():
    """Main function to process ideas from file"""
    ideas_file = DATA_DIR / "ideas.txt"

    if not ideas_file.exists():
        cprint("❌ ideas.txt not found! Creating template...", "red")
        ideas_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ideas_file, "w") as f:
            f.write("# Add your trading ideas here (one per line)\n")
            f.write("# Can be YouTube URLs, PDF links, or text descriptions\n")
        return

    with open(ideas_file, "r") as f:
        ideas = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    total_ideas = len(ideas)
    cprint(f"\n🎯 Found {total_ideas} trading ideas to process", "cyan")

    for i, idea in enumerate(ideas, 1):
        cprint(f"\n{'='*100}", "yellow")
        cprint(f"🌙 Processing idea {i}/{total_ideas}", "cyan")
        cprint(
            f"📝 Idea content: {idea[:100]}{'...' if len(idea) > 100 else ''}", "yellow"
        )
        cprint(f"{'='*100}\n", "yellow")

        try:
            # Process each idea in complete isolation
            process_trading_idea(idea)

            # Clear separator between ideas
            cprint(f"\n{'='*100}", "green")
            cprint(f"✅ Completed idea {i}/{total_ideas}", "green")
            cprint(f"{'='*100}\n", "green")

            # Break between ideas
            if i < total_ideas:
                cprint("😴 Taking a break before next idea...", "yellow")
                time.sleep(5)

        except Exception as e:
            cprint(f"\n❌ Error processing idea {i}: {str(e)}", "red")
            cprint("🔄 Continuing with next idea...\n", "yellow")
            continue


if __name__ == "__main__":
    try:
        cprint(f"\n🌟 Moon Dev's RBI Agent Starting Up!", "green")
        cprint(f"🤖 Using Research Model: {RESEARCH_MODEL}", "cyan")
        cprint(f"📊 Using Backtest Model: {BACKTEST_MODEL}", "cyan")
        cprint(f"🔧 Using Debug Model: {DEBUG_MODEL}", "cyan")
        main()
    except KeyboardInterrupt:
        cprint("\n👋 Moon Dev's RBI Agent shutting down gracefully...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
