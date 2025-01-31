"""
🌙 Moon Dev's Nice Functions - A collection of utility functions for trading
Built with love by Moon Dev 🚀
"""

from src.config import *
import requests
import pandas as pd
import pprint
import re as reggie
import math
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
import base64
from solana.rpc.types import TxOpts, TokenAccountOpts

# Load environment variables
load_dotenv()

# Get API keys and RPC endpoint from environment
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
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

# Utility Functions
def print_pretty_json(data):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data)

def find_urls(string):
    return reggie.findall(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        string,
    )

def round_down(value, decimals):
    factor = 10**decimals
    return math.floor(value * factor) / factor

def get_time_range(days_back):
    now = datetime.now()
    earlier = now - timedelta(days=days_back)
    time_to = int(now.timestamp())
    time_from = int(earlier.timestamp())
    return time_from, time_to

# Token Information Functions
def token_price(token_id):
    """Fetch the current price of a token using CoinGecko API."""
    url = f"{COINGECKO_BASE_URL}/simple/price"
    params = {"ids": token_id, "vs_currencies": "usd"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        price_data = response.json()
        return price_data.get(token_id, {}).get("usd", None)
    else:
        print(f"❌ Failed to fetch price for {token_id}. Status code: {response.status_code}")
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

def token_overview(address):
    """
    Fetch token overview for a given address and return structured information using RPC
    """
    print(f'Getting the token overview for {address}')
    result = {}

    try:
        # Get token metadata
        metadata = get_token_metadata(address)
        result['decimals'] = metadata.get('decimals', 9)

        # Get token security info
        payload_security = {
            "jsonrpc": "2.0",
            "id": "my-id",
            "method": "getTokenSecurity",
            "params": [address],
        }
        security_response = requests.post(RPC_ENDPOINT, json=payload_security)
        if security_response.status_code == 200:
            security_data = security_response.json().get('result', {})
            result['security'] = security_data

        # Get token creation info
        payload_creation = {
            "jsonrpc": "2.0",
            "id": "my-id",
            "method": "getTokenMint",
            "params": [address],
        }
        creation_response = requests.post(RPC_ENDPOINT, json=payload_creation)
        if creation_response.status_code == 200:
            creation_data = creation_response.json().get('result', {})
            result['creation'] = creation_data

        # Get token supply info
        pubkey = Pubkey.from_string(address)
        supply_response = solana_client.get_token_supply(pubkey)
        if supply_response:
            result['total_supply'] = supply_response.value.amount
            result['supply_decimals'] = supply_response.value.decimals

        # Extract links from metadata if available
        if 'creation' in result and 'metadata' in result['creation']:
            description = result['creation'].get('metadata', {}).get('data', {}).get('description', '')
            urls = find_urls(description)
            
            links = []
            for url in urls:
                if 't.me' in url:
                    links.append({'telegram': url})
                elif 'twitter.com' in url:
                    links.append({'twitter': url})
                elif 'youtube' not in url:
                    links.append({'website': url})
                    
            result['links'] = links

        return result

    except Exception as e:
        print(f"Error retrieving token overview for {address}: {str(e)}")
        return None


# Market Functions
def market_buy(token, amount, slippage):
    KEY = Keypair.from_base58_string(os.getenv("SOLANA_PRIVATE_KEY"))
    if not KEY:
        raise ValueError("🚨 SOLANA_PRIVATE_KEY not found in environment variables!")
    
    QUOTE_TOKEN = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
    http_client = Client(os.getenv("RPC_ENDPOINT"))
    
    if not http_client:
        raise ValueError("🚨 RPC_ENDPOINT not found in environment variables!")

    quote = requests.get(
        f"https://quote-api.jup.ag/v6/quote?inputMint={QUOTE_TOKEN}&outputMint={token}&amount={amount}&slippageBps={slippage}"
    ).json()

    txRes = requests.post(
        "https://quote-api.jup.ag/v6/swap",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "quoteResponse": quote,
            "userPublicKey": str(KEY.pubkey()),
            "prioritizationFeeLamports": PRIORITY_FEE,
        }),
    ).json()

    swapTx = base64.b64decode(txRes["swapTransaction"])
    tx1 = VersionedTransaction.from_bytes(swapTx)
    tx = VersionedTransaction(tx1.message, [KEY])
    txId = http_client.send_raw_transaction(bytes(tx), TxOpts(skip_preflight=True)).value
    print(f"https://solscan.io/tx/{str(txId)}")

def market_sell(QUOTE_TOKEN, amount, slippage):
    KEY = Keypair.from_base58_string(os.getenv("SOLANA_PRIVATE_KEY"))
    if not KEY:
        raise ValueError("🚨 SOLANA_PRIVATE_KEY not found in environment variables!")
    
    token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
    http_client = Client(os.getenv("RPC_ENDPOINT"))
    
    if not http_client:
        raise ValueError("🚨 RPC_ENDPOINT not found in environment variables!")

    quote = requests.get(
        f"https://quote-api.jup.ag/v6/quote?inputMint={QUOTE_TOKEN}&outputMint={token}&amount={amount}&slippageBps={slippage}"
    ).json()

    txRes = requests.post(
        "https://quote-api.jup.ag/v6/swap",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "quoteResponse": quote,
            "userPublicKey": str(KEY.pubkey()),
            "prioritizationFeeLamports": PRIORITY_FEE,
        }),
    ).json()

    swapTx = base64.b64decode(txRes["swapTransaction"])
    tx1 = VersionedTransaction.from_bytes(swapTx)
    tx = VersionedTransaction(tx1.message, [KEY])
    txId = http_client.send_raw_transaction(bytes(tx), TxOpts(skip_preflight=True)).value
    print(f"https://solscan.io/tx/{str(txId)}")

# Wallet and Position Functions
def fetch_wallet_token_single(wallet_address, token_mint_address):
    """Fetch the balance of a specific token for a wallet using RPC."""
    balances = fetch_wallet_balances(wallet_address)
    if balances.empty:
        return pd.DataFrame()

    # Filter for the specific token
    token_balance = balances[balances["Mint Address"] == token_mint_address]
    
    # Get price and calculate USD value
    if not token_balance.empty:
        price = token_price(token_mint_address) or 0
        token_balance["USD Value"] = token_balance["Balance"] * price
        
    return token_balance

def fetch_wallet_balances(wallet_address):
    """Fetch all token balances for a wallet using Solana RPC."""
    try:
        pubkey = Pubkey.from_string(wallet_address)
        opts = TokenAccountOpts(
            program_id=Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        )
        
        response = solana_client.get_token_accounts_by_owner(pubkey, opts)
        if not response.value:
            print("❌ No token accounts found for this wallet.")
            return pd.DataFrame()

        balances = []
        for account in response.value:
            try:
                raw_data = account.account.data
                if isinstance(raw_data, bytes):
                    mint_address = str(account.account.owner)
                    balance = 0
                    decimals = 9
                else:
                    account_info = raw_data.parsed["info"]
                    mint_address = account_info["mint"]
                    balance = int(account_info["tokenAmount"]["amount"])
                    decimals = int(account_info["tokenAmount"]["decimals"])

                balances.append({
                    "Mint Address": mint_address,
                    "Balance": balance / (10**decimals)
                })
            except Exception as e:
                print(f"🔍 Skipping account due to parsing: {str(e)[:100]}")
                continue

        return pd.DataFrame(balances)
    except Exception as e:
        print(f"❌ Error fetching wallet balances: {str(e)}")
        return pd.DataFrame()

def fetch_wallet_holdings_og(wallet_address):
    """Fetch wallet holdings with USD values using RPC and CoinGecko."""
    balances = fetch_wallet_balances(wallet_address)
    if balances.empty:
        return pd.DataFrame()

    balances["USD Value"] = balances.apply(
        lambda row: row["Balance"] * (token_price(row["Mint Address"]) or 0), 
        axis=1
    )

    return balances

def get_position(wallet_address, token_mint_address):
    """Fetch the balance of a specific token for a wallet using RPC."""
    balances = fetch_wallet_balances(wallet_address)
    if balances.empty:
        return 0

    token_balance = balances[balances["Mint Address"] == token_mint_address]
    if token_balance.empty:
        return 0

    return token_balance["Balance"].iloc[0]

def get_token_metadata(token_mint_address):
    """Fetch token metadata using Solana RPC."""
    try:
        pubkey = Pubkey.from_string(token_mint_address)
        response = solana_client.get_account_info(pubkey, encoding="jsonParsed")

        if not response.value:
            print(f"📝 No data found for: {token_mint_address}")
            return {"decimals": 9}

        if isinstance(response.value.data, bytes):
            return {"decimals": 9}

        metadata = response.value.data.parsed["info"]
        return {"decimals": metadata.get("decimals", 9)}

    except Exception as e:
        print(f"📝 Using default metadata for {token_mint_address}")
        return {"decimals": 9}

def get_decimals(token_mint_address):
    """Fetch token decimals using Solana RPC."""
    metadata = get_token_metadata(token_mint_address)
    if metadata:
        return metadata.get("decimals", 0)
    return 0

def get_token_balance_usd(token_mint_address):
    """Get USD value of token position"""
    try:
        df = fetch_wallet_token_single(address, token_mint_address)
        price = token_price(token_mint_address)
        if not price:
            return 0.0
        usd_value = df["USD Value"].iloc[0]
        return float(usd_value)
    except Exception as e:
        print(f"❌ Error getting token balance: {str(e)}")
        return 0.0

# Position Management Functions
def pnl_close(token_mint_address):
    """Check if it's time to exit a position based on PnL."""
    balance = get_position(address, token_mint_address)
    price = token_price(token_mint_address)
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

def chunk_kill(token_mint_address, max_usd_order_size, slippage):
    """Kill a position in chunks."""
    cprint(f"\n🔪 Moon Dev's AI Agent initiating position exit...", "white", "on_cyan")

    try:
        df = fetch_wallet_token_single(address, token_mint_address)
        if df.empty:
            cprint("❌ No position found to exit", "white", "on_red")
            return

        token_amount = float(df["Balance"].iloc[0])
        current_usd_value = float(df["USD Value"].iloc[0])
        decimals = get_decimals(token_mint_address)

        while current_usd_value > 0.1:
            chunk_size = token_amount / 3
            for i in range(3):
                try:
                    sell_size = int(chunk_size * 10**decimals)
                    market_sell(token_mint_address, sell_size, slippage)
                    time.sleep(2)
                except Exception as e:
                    cprint(f"❌ Error in sell chunk: {str(e)}", "white", "on_red")

            time.sleep(5)
            df = fetch_wallet_token_single(address, token_mint_address)
            if df.empty:
                return

            token_amount = float(df["Balance"].iloc[0])
            current_usd_value = float(df["USD Value"].iloc[0])

    except Exception as e:
        cprint(f"❌ Error during position exit: {str(e)}", "white", "on_red")

def elegant_entry(symbol, buy_under):
    """Execute an elegant entry."""
    pos = get_position(symbol)
    price = token_price(symbol)
    pos_usd = pos * price
    size_needed = usd_size - pos_usd
    chunk_size = min(size_needed, max_usd_order_size)
    chunk_size = int(chunk_size * 10**6)

    if pos_usd > (0.97 * usd_size):
        print("position filled")
        return

    while pos_usd < (0.97 * usd_size) and (price < buy_under):
        try:
            for i in range(orders_per_open):
                market_buy(symbol, chunk_size, slippage)
                time.sleep(1)

            time.sleep(tx_sleep)
            pos = get_position(symbol)
            price = token_price(symbol)
            pos_usd = pos * price
            size_needed = usd_size - pos_usd
            chunk_size = min(size_needed, max_usd_order_size)
            chunk_size = int(chunk_size * 10**6)

        except Exception:
            try:
                time.sleep(30)
                for i in range(orders_per_open):
                    market_buy(symbol, chunk_size, slippage)
                    time.sleep(1)

                time.sleep(tx_sleep)
                pos = get_position(symbol)
                price = token_price(symbol)
                pos_usd = pos * price
                size_needed = usd_size - pos_usd
                chunk_size = min(size_needed, max_usd_order_size)
                chunk_size = int(chunk_size * 10**6)

            except:
                cprint(f"Final Error in the buy, restart needed", "white", "on_red")
                time.sleep(10)
                break

def ai_entry(symbol, amount):
    """AI agent entry function for Moon Dev's trading system 🤖"""
    target_size = amount
    pos = get_position(symbol)
    price = token_price(symbol)
    pos_usd = pos * price

    if pos_usd >= (target_size * 0.97):
        cprint("✋ Position already at or above target size!", "white", "on_blue")
        return

    size_needed = target_size - pos_usd
    if size_needed <= 0:
        cprint("🛑 No additional size needed", "white", "on_blue")
        return

    chunk_size = min(size_needed, max_usd_order_size)
    chunk_size = int(chunk_size * 10**6)

    while pos_usd < (target_size * 0.97):
        try:
            for i in range(orders_per_open):
                market_buy(symbol, chunk_size, slippage)
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

            chunk_size = min(size_needed, max_usd_order_size)
            chunk_size = int(chunk_size * 10**6)

        except Exception:
            try:
                time.sleep(30)
                for i in range(orders_per_open):
                    market_buy(symbol, chunk_size, slippage)
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

                chunk_size = min(size_needed, max_usd_order_size)
                chunk_size = int(chunk_size * 10**6)

            except:
                cprint("❌ AI Agent encountered critical error", "white", "on_red")
                return

    cprint("✨ AI Agent completed position entry", "white", "on_blue")
