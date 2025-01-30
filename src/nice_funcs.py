"""
🌙 Moon Dev's Nice Functions - A collection of utility functions for trading
Built with love by Moon Dev 🚀
"""

from src.config import *
import requests
import pandas as pd
import pprint
import re as reggie
import sys
import os
import time
import json
import numpy as np
import datetime
import pandas_ta as ta
from datetime import datetime, timedelta
from termcolor import colored, cprint
from dotenv import load_dotenv
import shutil
import atexit
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client
import sys
import json
import base64
from solana.rpc.api import Client
from solana.rpc.types import TxOpts, TokenAccountOpts
from solana.rpc.types import TxOpts, TokenAccountOpts
from solana.rpc.types import TxOpts

# Load environment variables
load_dotenv()

# Get API keys and RPC endpoint from environment
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")  # Optional for free tier
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT")
if not RPC_ENDPOINT:
    raise ValueError("🚨 RPC_ENDPOINT not found in environment variables!")

# Initialize Solana client
solana_client = Client(RPC_ENDPOINT)

# CoinGecko API base URL
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Create temp directory and register cleanup
os.makedirs("temp_data", exist_ok=True)


def cleanup_temp_data():
    if os.path.exists("temp_data"):
        print("🧹 Moon Dev cleaning up temporary data...")
        shutil.rmtree("temp_data")


atexit.register(cleanup_temp_data)


# Custom function to print JSON in a human-readable format
def print_pretty_json(data):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data)


# Helper function to find URLs in text
def find_urls(string):
    # Regex to extract URLs
    return reggie.findall(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        string,
    )


# Fetch token price using CoinGecko API
def token_price(token_id):
    """Fetch the current price of a token using CoinGecko API."""
    url = f"{COINGECKO_BASE_URL}/simple/price"
    params = {"ids": token_id, "vs_currencies": "usd"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        price_data = response.json()
        return price_data.get(token_id, {}).get("usd", None)
    else:
        print(
            f"❌ Failed to fetch price for {token_id}. Status code: {response.status_code}"
        )
        return None


def token_security_info(address):
    """Get token security info using Helius"""
    payload = {
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "getTokenSecurity",
        "params": [address],
    }

    response = requests.post(RPC_ENDPOINT, json=payload)

    if response.status_code == 200:
        security_data = response.json().get("result", {})
        print_pretty_json(security_data)
    else:
        print("Failed to retrieve token security info:", response.status_code)


def token_creation_info(address):
    """Get token creation info using Helius"""
    payload = {
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "getTokenMint",
        "params": [address],
    }

    response = requests.post(RPC_ENDPOINT, json=payload)

    if response.status_code == 200:
        creation_data = response.json().get("result", {})
        print_pretty_json(creation_data)
    else:
        print("Failed to retrieve token creation info:", response.status_code)


def market_buy(token, amount, slippage):
    KEY = Keypair.from_base58_string(os.getenv("SOLANA_PRIVATE_KEY"))
    if not KEY:
        raise ValueError("🚨 SOLANA_PRIVATE_KEY not found in environment variables!")
    # print('key success')
    SLIPPAGE = slippage  # 5000 is 50%, 500 is 5% and 50 is .5%

    QUOTE_TOKEN = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # usdc

    http_client = Client(os.getenv("RPC_ENDPOINT"))
    # print('http client success')
    if not http_client:
        raise ValueError("🚨 RPC_ENDPOINT not found in environment variables!")

    quote = requests.get(
        f"https://quote-api.jup.ag/v6/quote?inputMint={QUOTE_TOKEN}&outputMint={token}&amount={amount}&slippageBps={SLIPPAGE}"
    ).json()
    # print(quote)

    txRes = requests.post(
        "https://quote-api.jup.ag/v6/swap",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "quoteResponse": quote,
                "userPublicKey": str(KEY.pubkey()),
                "prioritizationFeeLamports": PRIORITY_FEE,  # or replace 'auto' with your specific lamport value
            }
        ),
    ).json()
    # print(txRes)
    swapTx = base64.b64decode(txRes["swapTransaction"])
    # print(swapTx)
    tx1 = VersionedTransaction.from_bytes(swapTx)
    tx = VersionedTransaction(tx1.message, [KEY])
    txId = http_client.send_raw_transaction(
        bytes(tx), TxOpts(skip_preflight=True)
    ).value
    print(f"https://solscan.io/tx/{str(txId)}")


def market_sell(QUOTE_TOKEN, amount, slippage):
    KEY = Keypair.from_base58_string(os.getenv("SOLANA_PRIVATE_KEY"))
    if not KEY:
        raise ValueError("🚨 SOLANA_PRIVATE_KEY not found in environment variables!")
    # print('key success')
    SLIPPAGE = slippage  # 5000 is 50%, 500 is 5% and 50 is .5%

    # token would be usdc for sell orders cause we are selling
    token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC

    http_client = Client(os.getenv("RPC_ENDPOINT"))
    if not http_client:
        raise ValueError("🚨 RPC_ENDPOINT not found in environment variables!")
    print("http client success")

    quote = requests.get(
        f"https://quote-api.jup.ag/v6/quote?inputMint={QUOTE_TOKEN}&outputMint={token}&amount={amount}&slippageBps={SLIPPAGE}"
    ).json()
    # print(quote)
    txRes = requests.post(
        "https://quote-api.jup.ag/v6/swap",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "quoteResponse": quote,
                "userPublicKey": str(KEY.pubkey()),
                "prioritizationFeeLamports": PRIORITY_FEE,
            }
        ),
    ).json()
    # print(txRes)
    swapTx = base64.b64decode(txRes["swapTransaction"])
    # print(swapTx)
    tx1 = VersionedTransaction.from_bytes(swapTx)
    # print(tx1)
    tx = VersionedTransaction(tx1.message, [KEY])
    # print(tx)
    txId = http_client.send_raw_transaction(
        bytes(tx), TxOpts(skip_preflight=True)
    ).value
    print(f"https://solscan.io/tx/{str(txId)}")


import math


def round_down(value, decimals):
    factor = 10**decimals
    return math.floor(value * factor) / factor


def get_time_range(days_back):
    now = datetime.now()
    ten_days_earlier = now - timedelta(days=days_back)
    time_to = int(now.timestamp())
    time_from = int(ten_days_earlier.timestamp())
    # print(time_from, time_to)

    return time_from, time_to


def get_data(address, days_back=DAYSBACK_4_DATA, timeframe=timeframe):
    # Check temp data first
    temp_file = f"moondev/temp_data/{address}_latest.csv"
    if os.path.exists(temp_file):
        print(f"📂 Moon Dev found cached data for {address[:4]}")
        return pd.read_csv(temp_file)

    # Map timeframe to CoinGecko's interval
    interval_map = {"1h": "hourly", "1d": "daily"}
    interval = interval_map.get(timeframe, "daily")

    # Construct the URL for historical market data
    url = f"{COINGECKO_BASE_URL}/coins/solana/contract/{address}/market_chart?vs_currency=usd&days={days_back}&interval={interval}"

    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": COINGECKO_API_KEY,
    }

    # Fetch historical market data
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        market_data = response.json()
        prices = market_data.get("prices", [])

        # Create DataFrame from prices
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["Datetime (UTC)"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.drop("timestamp", axis=1)

        # Calculate OHLCV data (if not provided by CoinGecko)
        df["Open"] = df["price"].shift(1)  # Open = Previous Close
        df["High"] = df["price"].rolling(window=len(df), min_periods=1).max()
        df["Low"] = df["price"].rolling(window=len(df), min_periods=1).min()
        df["Close"] = df["price"]
        df["Volume"] = 0  # CoinGecko doesn't provide volume data for contract addresses

        # Remove any rows with dates far in the future
        current_date = datetime.now()
        df = df[df["Datetime (UTC)"] <= current_date]

        # Pad if needed
        if len(df) < 40:
            print(
                f"🌙 MoonDev Alert: Padding data to ensure minimum 40 rows for analysis! 🚀"
            )
            rows_to_add = 40 - len(df)
            first_row_replicated = pd.concat(
                [df.iloc[0:1]] * rows_to_add, ignore_index=True
            )
            df = pd.concat([first_row_replicated, df], ignore_index=True)

        print(f"📊 MoonDev's Data Analysis Ready! Processing {len(df)} candles... 🎯")

        # Always save to temp for current run
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        df.to_csv(temp_file, index=False)
        print(f"🔄 Moon Dev cached data for {address[:4]}")

        # Calculate technical indicators
        df["MA20"] = ta.sma(df["Close"], length=20)
        df["RSI"] = ta.rsi(df["Close"], length=14)
        df["MA40"] = ta.sma(df["Close"], length=40)
        print(f"🔄 Moon Dev cached data for {address[:4]}")

        # Calculate technical indicators
        df["MA20"] = ta.sma(df["Close"], length=20)
        df["RSI"] = ta.rsi(df["Close"], length=14)
        df["MA40"] = ta.sma(df["Close"], length=40)

        df["Price_above_MA20"] = df["Close"] > df["MA20"]
        df["Price_above_MA40"] = df["Close"] > df["MA40"]
        df["MA20_above_MA40"] = df["MA20"] > df["MA40"]

        return df
    else:
        print(
            f"❌ Failed to fetch market data for {address}. Status code: {response.status_code}"
        )
        if response.status_code == 401:
            print("🔑 Check your CoinGecko API key in the .env file!")
        return pd.DataFrame()


# Fetch wallet balances using Solana RPC
def fetch_wallet_balances(wallet_address):
    """Fetch all token balances for a wallet using Solana RPC."""
    try:
        # Convert wallet address to Pubkey
        pubkey = Pubkey.from_string(wallet_address)

        # Define the token account options
        opts = TokenAccountOpts(
            program_id=Pubkey.from_string(
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
            )  # SPL Token Program ID
        )

        response = solana_client.get_token_accounts_by_owner(pubkey, opts)

        # Fetch token accounts
        if not response.value:
            print("❌ No token accounts found for this wallet.")
            return pd.DataFrame()

        # Parse token accounts
        balances = []
        for account in response.value:
            try:
                raw_data = account.account.data
                if isinstance(raw_data, bytes):
                    # Handle raw bytes data
                    mint_address = str(account.account.owner)
                    balance = 0
                    decimals = 9
                else:
                    # Handle parsed data
                    account_info = raw_data.parsed["info"]
                    mint_address = account_info["mint"]
                    balance = int(account_info["tokenAmount"]["amount"])
                    decimals = int(account_info["tokenAmount"]["decimals"])

                balances.append(
                    {"Mint Address": mint_address, "Balance": balance / (10**decimals)}
                )
            except Exception as e:
                print(f"🔍 Skipping account due to parsing: {str(e)[:100]}")
                continue

        return pd.DataFrame(balances)
    except Exception as e:
        print(f"❌ Error fetching wallet balances: {str(e)}")
        return pd.DataFrame()


# Fetch wallet holdings with USD values
def fetch_wallet_holdings_og(wallet_address):
    """Fetch wallet holdings with USD values using RPC and CoinGecko."""
    balances = fetch_wallet_balances(wallet_address)
    if balances.empty:
        return pd.DataFrame()

    # Add USD value for each token
    balances["USD Value"] = balances.apply(
        lambda row: row["Balance"] * (token_price(row["Mint Address"]) or 0), 
        axis=1
    )

    return balances


# Get position balance for a specific token
def get_position(wallet_address, token_mint_address):
    """Fetch the balance of a specific token for a wallet using RPC."""
    balances = fetch_wallet_balances(wallet_address)
    if balances.empty:
        return 0

    # Filter for the specific token
    token_balance = balances[balances["Mint Address"] == token_mint_address]
    if token_balance.empty:
        return 0

    return token_balance["Balance"].iloc[0]


# Fetch token metadata using Solana RPC
def get_token_metadata(token_mint_address):
    """Fetch token metadata (e.g., decimals) using Solana RPC."""
    try:
        pubkey = Pubkey.from_string(token_mint_address)
        response = solana_client.get_account_info(
            pubkey, encoding="jsonParsed"  # Explicitly request parsed format
        )

        if not response.value:
            print(f"📝 No data found for: {token_mint_address}")
            return {"decimals": 9}  # Return default decimals

        # Handle raw bytes response
        if isinstance(response.value.data, bytes):
            return {"decimals": 9}  # Use default decimals for raw data

        metadata = response.value.data.parsed["info"]
        return {"decimals": metadata.get("decimals", 9)}

    except Exception as e:
        print(f"📝 Using default metadata for {token_mint_address}")
        return {"decimals": 9}


# Check PnL and close position if necessary
def pnl_close(token_mint_address):
    """Check if it's time to exit a position based on PnL."""
    balance = get_position(address, token_mint_address)
    price = token_price(token_mint_address)  # Use CoinGecko for price
    usd_value = balance * price

    tp = sell_at_multiple * USDC_SIZE
    sl = (1 + stop_loss_perctentage) * USDC_SIZE

    if usd_value > tp:
        print(f"🚀 Taking profit for {token_mint_address[:4]}...")
        market_sell(token_mint_address, balance, slippage)
    elif usd_value < sl:
        print(f"📉 Stopping loss for {token_mint_address[:4]}...")
        market_sell(token_mint_address, balance, slippage)


# Get position balance for a specific token
def get_position(wallet_address, token_mint_address):
    """Fetch the balance of a specific token for a wallet using RPC."""
    balances = fetch_wallet_balances(wallet_address)
    if balances.empty:
        return 0

    # Filter for the specific token
    token_balance = balances[balances["Mint Address"] == token_mint_address]
    if token_balance.empty:
        return 0

    return token_balance["Balance"].iloc[0]


# Fetch token metadata using Solana RPC
def get_token_metadata(token_mint_address):
    """Fetch token metadata (e.g., decimals) using Solana RPC."""
    try:
        # Convert mint address to Pubkey
        pubkey = Pubkey.from_string(token_mint_address)

        # Fetch account info
        response = solana_client.get_account_info(pubkey)
        if not response.value:
            print(f"❌ No account info found for mint address: {token_mint_address}")
            return None

        # Parse metadata (decimals)
        metadata = response.value.data.parsed["info"]
        return {"decimals": metadata.get("decimals", 0)}

    except Exception as e:
        print(f"❌ Error fetching token metadata: {str(e)}")
        return None


# Check PnL and close position if necessary
def pnl_close(token_mint_address):
    """Check if it's time to exit a position based on PnL."""
    balance = get_position(address, token_mint_address)
    price = token_price(token_mint_address)  # Use CoinGecko for price
    usd_value = balance * price

    tp = sell_at_multiple * USDC_SIZE
    sl = (1 + stop_loss_perctentage) * USDC_SIZE

    if usd_value > tp:
        print(f"🚀 Taking profit for {token_mint_address[:4]}...")
        market_sell(token_mint_address, balance, slippage)
    elif usd_value < sl:
        print(f"📉 Stopping loss for {token_mint_address[:4]}...")
        market_sell(token_mint_address, balance, slippage)
    else:
        print(f"🔄 Holding position for {token_mint_address[:4]}...")


# Close all positions
def close_all_positions():
    """Close all positions in the wallet."""
    balances = fetch_wallet_balances(address)

    if balances.empty:
        print("❌ No positions to close.")
        return

    for _, row in balances.iterrows():
        token_mint_address = row["Mint Address"]
        balance = row["Balance"]
        print(f"🔪 Closing position for {token_mint_address[:4]}...")
        market_sell(token_mint_address, balance, slippage)


# Fetch wallet token single
def fetch_wallet_token_single(wallet_address, token_mint_address):
    """Fetch the balance of a specific token for a wallet using RPC."""
    balances = fetch_wallet_balances(wallet_address)
    if balances.empty:
        return pd.DataFrame()

    # Filter for the specific token
    token_balance = balances[balances["Mint Address"] == token_mint_address]
    return token_balance


# Get token decimals using Solana RPC
def get_decimals(token_mint_address):
    """Fetch token decimals using Solana RPC."""
    metadata = get_token_metadata(token_mint_address)
    if metadata:
        return metadata.get("decimals", 0)
    return 0


# Chunk kill a position
def chunk_kill(token_mint_address, max_usd_order_size, slippage):
    """Kill a position in chunks."""
    cprint(f"\n🔪 Moon Dev's AI Agent initiating position exit...", "white", "on_cyan")

    try:
        # Get current position using address from config
        df = fetch_wallet_token_single(address, token_mint_address)
        if df.empty:
            cprint("❌ No position found to exit", "white", "on_red")
            return

        # Get current token amount and value
        token_amount = float(df["Balance"].iloc[0])
        current_usd_value = float(df["USD Value"].iloc[0])

        # Get token decimals
        decimals = get_decimals(token_mint_address)

        cprint(
            f"📊 Initial position: {token_amount:.2f} tokens (${current_usd_value:.2f})",
            "white",
            "on_cyan",
        )

        while current_usd_value > 0.1:  # Keep going until position is essentially zero
            # Calculate chunk size based on current position
            chunk_size = token_amount / 3  # Split remaining into 3 chunks
            cprint(
                f"\n🔄 Splitting remaining position into chunks of {chunk_size:.2f} tokens",
                "white",
                "on_cyan",
            )

            # Execute sell orders in chunks
            for i in range(3):
                try:
                    cprint(f"\n💫 Executing sell chunk {i+1}/3...", "white", "on_cyan")
                    sell_size = int(chunk_size * 10**decimals)
                    market_sell(token_mint_address, sell_size, slippage)
                    cprint(f"✅ Sell chunk {i+1}/3 complete", "white", "on_green")
                    time.sleep(2)  # Small delay between chunks
                except Exception as e:
                    cprint(f"❌ Error in sell chunk: {str(e)}", "white", "on_red")

            # Check remaining position
            time.sleep(5)  # Wait for blockchain to update
            df = fetch_wallet_token_single(address, token_mint_address)
            if df.empty:
                cprint("\n✨ Position successfully closed!", "white", "on_green")
                return

            # Update position size for next iteration
            token_amount = float(df["Balance"].iloc[0])
            current_usd_value = float(df["USD Value"].iloc[0])
            cprint(
                f"\n📊 Remaining position: {token_amount:.2f} tokens (${current_usd_value:.2f})",
                "white",
                "on_cyan",
            )

            if current_usd_value > 0.1:
                cprint(
                    "🔄 Position still open - continuing to close...",
                    "white",
                    "on_cyan",
                )
                time.sleep(2)

        cprint("\n✨ Position successfully closed!", "white", "on_green")

    except Exception as e:
        cprint(f"❌ Error during position exit: {str(e)}", "white", "on_red")


# Sell token
def sell_token(token_mint_address, amount, slippage):
    """Sell a token."""
    try:
        cprint(f"📉 Selling {amount:.2f} tokens...", "white", "on_cyan")
        market_sell(token_mint_address, amount, slippage)
    except Exception as e:
        cprint(f"❌ Error selling token: {str(e)}", "white", "on_red")


# Kill switch
def kill_switch(token_mint_address):
    """Close a position in full."""
    balance = get_position(address, token_mint_address)
    if balance <= 0:
        print(f"❌ No position to close for {token_mint_address[:4]}.")
        return

    print(f"🔪 Closing position for {token_mint_address[:4]}...")
    market_sell(token_mint_address, balance, slippage)


# Delete dont_overtrade file
def delete_dont_overtrade_file():
    if os.path.exists("dont_overtrade.txt"):
        os.remove("dont_overtrade.txt")
        print("dont_overtrade.txt has been deleted")
    else:
        print("The file does not exist")


def get_time_range():
    now = datetime.now()
    ten_days_earlier = now - timedelta(days=10)
    time_to = int(now.timestamp())
    time_from = int(ten_days_earlier.timestamp())
    # print(time_from, time_to)

    return time_from, time_to


import math


def round_down(value, decimals):
    factor = 10**decimals
    return math.floor(value * factor) / factor


# Supply and demand zones
def supply_demand_zones(token_address, timeframe, limit):
    """Calculate supply and demand zones."""
    print("Starting supply and demand zone calculations...")
    sd_df = pd.DataFrame()

    time_from, time_to = get_time_range()

    df = get_data(token_address, time_from, time_to, timeframe)

    # Only keep the data for as many bars as limit says
    df = df[-limit:]

    # Calculate support and resistance
    if len(df) > 2:
        df["support"] = df[:-2]["Close"].min()
        df["resis"] = df[:-2]["Close"].max()
    else:
        df["support"] = df["Close"].min()
        df["resis"] = df["Close"].max()

    supp = df.iloc[-1]["support"]
    resis = df.iloc[-1]["resis"]

    df["supp_lo"] = df[:-2]["Low"].min()
    supp_lo = df.iloc[-1]["supp_lo"]

    df["res_hi"] = df[:-2]["High"].max()
    res_hi = df.iloc[-1]["res_hi"]

    sd_df[f"dz"] = [supp_lo, supp]
    sd_df[f"sz"] = [res_hi, resis]

    print("Supply and demand zones calculated.")
    return sd_df


# Elegant entry
def elegant_entry(symbol, buy_under):
    """Execute an elegant entry."""
    pos = get_position(symbol)
    price = token_price(symbol)
    pos_usd = pos * price
    size_needed = usd_size - pos_usd
    if size_needed > max_usd_order_size:
        chunk_size = max_usd_order_size
    else:
        chunk_size = size_needed

    chunk_size = int(chunk_size * 10**6)

    print(f"chunk_size: {chunk_size}")

    if pos_usd > (0.97 * usd_size):
        print("position filled")
        time.sleep(10)

    # Add debug prints for next while
    print(
        f"position: {round(pos,2)} price: {round(price,8)} pos_usd: ${round(pos_usd,2)}"
    )
    print(f"buy_under: {buy_under}")
    while pos_usd < (0.97 * usd_size) and (price < buy_under):

        print(
            f"position: {round(pos,2)} price: {round(price,8)} pos_usd: ${round(pos_usd,2)}"
        )

        try:

            for i in range(orders_per_open):
                market_buy(symbol, chunk_size, slippage)
                # cprint green background black text
                cprint(
                    f"chunk buy submitted of {symbol[:4]} sz: {chunk_size} you my dawg moon dev",
                    "white",
                    "on_blue",
                )
                time.sleep(1)

            time.sleep(tx_sleep)

            pos = get_position(symbol)
            price = token_price(symbol)
            pos_usd = pos * price
            size_needed = usd_size - pos_usd
            if size_needed > max_usd_order_size:
                chunk_size = max_usd_order_size
            else:
                chunk_size = size_needed
            chunk_size = int(chunk_size * 10**6)

        except:

            try:
                cprint(
                    f"trying again to make the order in 30 seconds.....",
                    "light_blue",
                    "on_light_magenta",
                )
                time.sleep(30)
                for i in range(orders_per_open):
                    market_buy(symbol, chunk_size, slippage)
                    # cprint green background black text
                    cprint(
                        f"chunk buy submitted of {symbol[:4]} sz: {chunk_size} you my dawg moon dev",
                        "white",
                        "on_blue",
                    )
                    time.sleep(1)

                time.sleep(tx_sleep)
                pos = get_position(symbol)
                price = token_price(symbol)
                pos_usd = pos * price
                size_needed = usd_size - pos_usd
                if size_needed > max_usd_order_size:
                    chunk_size = max_usd_order_size
                else:
                    chunk_size = size_needed
                chunk_size = int(chunk_size * 10**6)

            except:
                cprint(f"Final Error in the buy, restart needed", "white", "on_red")
                time.sleep(10)
                break

        pos = get_position(symbol)
        price = token_price(symbol)
        pos_usd = pos * price
        size_needed = usd_size - pos_usd
        if size_needed > max_usd_order_size:
            chunk_size = max_usd_order_size
        else:
            chunk_size = size_needed
        chunk_size = int(chunk_size * 10**6)


# Breakout entry
def breakout_entry(symbol, BREAKOUT_PRICE):
    """Execute a breakout entry."""
    pos = get_position(symbol)
    price = token_price(symbol)
    price = float(price)
    pos_usd = pos * price
    size_needed = usd_size - pos_usd
    if size_needed > max_usd_order_size:
        chunk_size = max_usd_order_size

    else:
        chunk_size = size_needed

    chunk_size = int(chunk_size * 10**6)
    chunk_size = str(chunk_size)

    print(f"chunk_size: {chunk_size}")

    if pos_usd > (0.97 * usd_size):
        print("position filled")
        time.sleep(10)

    # Add debug prints for next while
    print(
        f"position: {round(pos,2)} price: {round(price,8)} pos_usd: ${round(pos_usd,2)}"
    )
    print(f"breakoutpurce: {BREAKOUT_PRICE}")
    while pos_usd < (0.97 * usd_size) and (price > BREAKOUT_PRICE):
        print(
            f"position: {round(pos,2)} price: {round(price,8)} pos_usd: ${round(pos_usd,2)}"
        )

        try:

            for i in range(orders_per_open):
                market_buy(symbol, chunk_size, slippage)
                # cprint green background black text
                cprint(
                    f"chunk buy submitted of {symbol[:4]} sz: {chunk_size} you my dawg moon dev",
                    "white",
                    "on_blue",
                )
                time.sleep(1)

            time.sleep(tx_sleep)

            pos = get_position(symbol)
            price = token_price(symbol)
            pos_usd = pos * price
            size_needed = usd_size - pos_usd
            if size_needed > max_usd_order_size:
                chunk_size = max_usd_order_size

            else:
                chunk_size = size_needed
            chunk_size = int(chunk_size * 10**6)

        except:

            try:
                cprint(
                    f"trying again to make the order in 30 seconds.....",
                    "light_blue",
                    "on_light_magenta",
                )
                time.sleep(30)
                for i in range(orders_per_open):
                    market_buy(symbol, chunk_size, slippage)
                    # cprint green background black text
                    cprint(
                        f"chunk buy submitted of {symbol[:4]} sz: {chunk_size} you my dawg moon dev",
                        "white",
                        "on_blue",
                    )
                    time.sleep(1)

                time.sleep(tx_sleep)
                pos = get_position(symbol)
                price = token_price(symbol)
                pos_usd = pos * price
                size_needed = usd_size - pos_usd
                if size_needed > max_usd_order_size:
                    chunk_size = max_usd_order_size

                else:
                    chunk_size = size_needed
                chunk_size = int(chunk_size * 10**6)

            except:
                cprint(f"Final Error in the buy, restart needed", "white", "on_red")
                time.sleep(10)
                break

        pos = get_position(symbol)
        price = token_price(symbol)
        pos_usd = pos * price
        size_needed = usd_size - pos_usd
        if size_needed > max_usd_order_size:
            chunk_size = max_usd_order_size
        else:
            chunk_size = size_needed
        chunk_size = int(chunk_size * 10**6)


# AI entry
def ai_entry(symbol, amount):
    """AI agent entry function for Moon Dev's trading system 🤖"""
    cprint(
        "🤖 Moon Dev's AI Trading Agent initiating position entry...",
        "white",
        "on_blue",
    )

    # amount passed in is the target allocation (up to 30% of usd_size)
    target_size = amount  # This could be up to $3 (30% of $10)

    pos = get_position(symbol)
    price = token_price(symbol)
    pos_usd = pos * price

    cprint(
        f"🎯 Target allocation: ${target_size:.2f} USD (max 30% of ${usd_size})",
        "white",
        "on_blue",
    )
    cprint(f"📊 Current position: ${pos_usd:.2f} USD", "white", "on_blue")

    # Check if we're already at or above target
    if pos_usd >= (target_size * 0.97):
        cprint("✋ Position already at or above target size!", "white", "on_blue")
        return

    # Calculate how much more we need to buy
    size_needed = target_size - pos_usd
    if size_needed <= 0:
        cprint("🛑 No additional size needed", "white", "on_blue")
        return

    # For order execution, we'll chunk into max_usd_order_size pieces
    if size_needed > max_usd_order_size:
        chunk_size = max_usd_order_size
    else:
        chunk_size = size_needed

    chunk_size = int(chunk_size * 10**6)

    cprint(
        f"💫 Entry chunk size: {chunk_size} (chunking ${size_needed:.2f} into ${max_usd_order_size:.2f} orders)",
        "white",
        "on_blue",
    )

    while pos_usd < (target_size * 0.97):
        cprint(f"🤖 AI Agent executing entry for {symbol[:8]}...", "white", "on_blue")
        print(
            f"Position: {round(pos,2)} | Price: {round(price,8)} | USD Value: ${round(pos_usd,2)}"
        )

        try:
            for i in range(orders_per_open):
                market_buy(symbol, chunk_size, slippage)
                cprint(
                    f"🚀 AI Agent placed order {i+1}/{orders_per_open} for {symbol[:8]}",
                    "white",
                    "on_blue",
                )
                time.sleep(1)

            time.sleep(tx_sleep)
            # Update position info
            pos = get_position(symbol)
            price = token_price(symbol)
            pos_usd = pos * price

            # Break if we're at or above target
            if pos_usd >= (target_size * 0.97):
                break

            # Recalculate needed size
            size_needed = target_size - pos_usd
            if size_needed <= 0:
                break

            # Determine next chunk size
            if size_needed > max_usd_order_size:
                chunk_size = max_usd_order_size
            else:
                chunk_size = size_needed
            chunk_size = int(chunk_size * 10**6)
            chunk_size = str(chunk_size)

        except Exception as e:
            try:
                cprint(
                    "🔄 AI Agent retrying order in 30 seconds...", "white", "on_blue"
                )
                time.sleep(30)

                for i in range(orders_per_open):
                    market_buy(symbol, chunk_size, slippage)
                    cprint(
                        f"🚀 AI Agent retry order {i+1}/{orders_per_open} for {symbol[:8]}",
                        "white",
                        "on_blue",
                    )
                    time.sleep(1)

                time.sleep(tx_sleep)
                pos = get_position(symbol)
                price = token_price(symbol)
                pos_usd = pos * price

                if pos_usd >= (target_size * 0.97):
                    break

                size_needed = target_size - pos_usd
                if size_needed <= 0:
                    break

                if size_needed > max_usd_order_size:
                    chunk_size = max_usd_order_size
                else:
                    chunk_size = size_needed
                chunk_size = int(chunk_size * 10**6)
                chunk_size = str(chunk_size)

            except:
                cprint(
                    "❌ AI Agent encountered critical error, manual intervention needed",
                    "white",
                    "on_red",
                )
                return

    cprint("✨ AI Agent completed position entry", "white", "on_blue")


# Get token balance in USD
def get_token_balance_usd(token_mint_address):
    """Get USD value of token position"""
    try:
        df = fetch_wallet_token_single(address, token_mint_address)

        # Get price and calculate USD value
        price = token_price(token_mint_address)
        if not price:
            return 0.0

        # Get the USD Value from the dataframe
        usd_value = df["USD Value"].iloc[0]
        return float(usd_value)

    except Exception as e:
        print(f"❌ Error getting token balance: {str(e)}")
        return 0.0
