"""
🌙 Moon Dev's Whale Discovery Scanner
Finds high-volume Solana traders using Helius RPC
"""

import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import requests
from termcolor import colored, cprint
from datetime import datetime
import time

# Load environment variables
load_dotenv()

RPC_ENDPOINT = os.getenv("RPC_ENDPOINT")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuration
MIN_TRADE_VOLUME = 5  # Minimum SOL volume per trade
MIN_TRADES_COUNT = 2       # Minimum number of trades to qualify
OUTPUT_FILE = Path("moondev/src/data/discovered_whales.csv")

def get_recent_transactions():
    payload = {
        "jsonrpc": "2.0",
        "id": "get_txs",
        "method": "getSignaturesForAddress",
        "params": [
            "4k3DyjvWmYP3kRpn6f6CzW6b8A6bnkqB4P5XtTr4oi6B",  # Raydium
            {"limit": 1000}
        ]
    }
    
    response = requests.post(RPC_ENDPOINT, json=payload)
    return response.json()

def process_transactions(transactions):
    wallet_stats = {}

    for tx in transactions['result']:
        tx_details_payload = {
            "jsonrpc": "2.0",
            "id": "get_tx_details",
            "method": "getTransaction",
            "params": [
                tx['signature'],
                {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
            ]
        }
        
        tx_details = requests.post(RPC_ENDPOINT, json=tx_details_payload).json()
        
        if 'result' in tx_details and tx_details['result']:
            # Extract wallet address (sender)
            wallet = tx_details['result']['transaction']['message']['accountKeys'][0]['pubkey']
            
            # Calculate transaction value
            if 'meta' in tx_details['result'] and 'preBalances' in tx_details['result']['meta']:
                value = abs(tx_details['result']['meta']['preBalances'][0] - 
                          tx_details['result']['meta']['postBalances'][0]) / 1e9
                
                # Get token info from transaction
                token_info = None
                if 'meta' in tx_details['result']:
                    post_token_balances = tx_details['result']['meta'].get('postTokenBalances', [])
                    if post_token_balances:
                        token_info = post_token_balances[-1].get('mint')
                
                # Update wallet statistics
                if wallet not in wallet_stats:
                    wallet_stats[wallet] = {
                        'total_volume': 0,
                        'trade_count': 0,
                        'trades': [],
                        'first_seen': tx['blockTime'],
                        'last_seen': tx['blockTime'],
                        'last_token': token_info
                    }
                
                wallet_stats[wallet]['total_volume'] += value
                wallet_stats[wallet]['trade_count'] += 1
                wallet_stats[wallet]['trades'].append({
                    'timestamp': tx['blockTime'],
                    'value': value,
                    'token': token_info
                })
                wallet_stats[wallet]['last_seen'] = max(wallet_stats[wallet]['last_seen'], tx['blockTime'])
                if token_info:
                    wallet_stats[wallet]['last_token'] = token_info
    
    # Filter for whales based on criteria
    whales_data = []
    for wallet, stats in wallet_stats.items():
        if (stats['total_volume'] >= MIN_TRADE_VOLUME and 
            stats['trade_count'] >= MIN_TRADES_COUNT):
            whales_data.append({
                'wallet_address': wallet,
                'total_volume_sol': stats['total_volume'],
                'trade_count': stats['trade_count'],
                'avg_trade_size': stats['total_volume'] / stats['trade_count'],
                'first_seen': datetime.fromtimestamp(stats['first_seen']),
                'last_seen': datetime.fromtimestamp(stats['last_seen']),
                'last_token': stats['last_token']
            })
    
    return whales_data

def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.get(url, params=params)

    print(message)

def discover_whales():
    whales_data = []
    known_whales = set()  # Track already discovered whales
    
    while True:
        transactions = get_recent_transactions()
        new_whales = process_transactions(transactions)
        
        # Filter out already known whales
        new_whales = [whale for whale in new_whales if whale['wallet_address'] not in known_whales]
        
        if new_whales:
            # Add new whales to our tracking sets
            known_whales.update(whale['wallet_address'] for whale in new_whales)
            whales_data.extend(new_whales)
            
            # Update CSV with all whales
            whales_df = pd.DataFrame(whales_data)
            whales_df.sort_values('total_volume_sol', ascending=False, inplace=True)
            whales_df.to_csv(OUTPUT_FILE, index=False)
            
            cprint(f"🐋 Found {len(new_whales)} new whale wallet!", "green")
            cprint(f"📊 Total tracked whales: {len(whales_data)}", "blue")
            cprint(f"💰 Top whale volume: {whales_df['total_volume_sol'].max():.2f} SOL", "yellow")
        
            # Send alert for new whales
            for whale in new_whales:
                message = (f"🐋 New Whale Found!\n"
                           f"Wallet Address: {whale['wallet_address']}\n"
                           f"Total Volume: {whale['total_volume_sol']:.2f} SOL\n"
                           f"Trade Count: {whale['trade_count']}\n"
                           f"Average Trade Size: {whale['avg_trade_size']:.2f} SOL\n"
                           f"First Seen: {whale['first_seen']}\n"
                           f"Last Seen: {whale['last_seen']}\n"
                           f"Last Token: {whale['last_token']}")
                send_alert(message)  # Send the alert to Telegram

        cprint("🔍 Monitoring for new whale activity...", "cyan")
        time.sleep(15)  # Wait 15 seconds before next check
if __name__ == "__main__":
    discover_whales()
