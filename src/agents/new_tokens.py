import aiohttp
import asyncio
from datetime import datetime
import json
import csv
import time

DEXSCREENER_API = "https://api.dexscreener.com/token-profiles/latest/v1"
HISTORY_FILE = "last_token_scan.json"
OUTPUT_FILE = "moondev/src/agents/api_data/new_token_addresses_1.csv"

def save_token_data(token_data: dict):
    token_address = token_data['tokenAddress']
    epoch_time = int(time.time())
    time_found = datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')
    
    solscan_link = f"https://solscan.io/token/{token_address}"
    dexscreener_link = f"https://dexscreener.com/solana/{token_address}"
    birdeye_link = f"https://birdeye.so/token/{token_address}?chain=solana"
    
    with open(OUTPUT_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            token_address,
            time_found,
            epoch_time,
            solscan_link,
            dexscreener_link,
            birdeye_link
        ])

async def load_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'last_token': None, 'timestamp': None}

async def save_history(last_token):
    history = {
        'last_token': last_token,
        'timestamp': datetime.now().isoformat()
    }
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

async def scan_new_tokens():
    while True:
        try:
            history = await load_history()
            last_token = history['last_token']
            
            async with aiohttp.ClientSession() as session:
                async with session.get(DEXSCREENER_API) as response:
                    tokens = await response.json()
                    new_tokens_found = False
                    
                    for token in tokens:
                        if token['chainId'] == 'solana':
                            token_address = token['tokenAddress']
                            
                            if last_token and token_address == last_token:
                                break
                                
                            save_token_data(token)
                            new_tokens_found = True
                            print(f"🆕 New token found: {token_address}")
                            print(f"🔗 https://dexscreener.com/solana/{token_address}")
                    
                    if new_tokens_found and tokens:
                        await save_history(tokens[0]['tokenAddress'])
                    
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"Error scanning tokens: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # Create CSV header if file doesn't exist
    with open(OUTPUT_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow([
                'Token Address',
                'Time Found',
                'Epoch Time',
                'Solscan Link',
                'DexScreener Link',
                'Birdeye Link'
            ])
    
    asyncio.run(scan_new_tokens())
