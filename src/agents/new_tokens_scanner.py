import asyncio
import websockets
import json
import requests
import redis
import time

# Redis Setup
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# API Configurations
HELIUS_WSS_URL = "wss://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"
HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"
DEX_SCREENER_URL = "https://api.dexscreener.com/latest/dex/tokens/solana"

# Solana Token Program ID (Used for tracking token mints)
SPL_TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

async def get_transaction_details(signature):
    """Fetch full transaction details using Helius RPC"""
    headers = {'Content-Type': 'application/json'}
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            signature,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
        ]
    }
    
    response = requests.post(HELIUS_RPC_URL, headers=headers, json=request)
    return response.json()

async def get_token_info(mint_address):
    """Fetch token account info using Helius RPC"""
    headers = {'Content-Type': 'application/json'}
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            mint_address,
            {"encoding": "jsonParsed"}
        ]
    }
    
    response = requests.post(HELIUS_RPC_URL, headers=headers, json=request)
    return response.json()

async def monitor_new_tokens():
    while True:  # Outer loop for reconnection
        try:
            async with websockets.connect(HELIUS_WSS_URL) as ws:
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "logsSubscribe",
                    "params": [
                        {"mentions": [SPL_TOKEN_PROGRAM_ID]},
                        {"commitment": "finalized"}
                    ]
                }
                await ws.send(json.dumps(request))
                print("🔍 Listening for new token mints...")

                while True:  # Inner loop for message handling
                    response = await ws.recv()
                    data = json.loads(response)
                    # print(f"🔍 Received data: {data}")

                    if "params" in data and "result" in data["params"]:
                        if "err" in data["params"]["result"]["value"] and data["params"]["result"]["value"]["err"] is not None:
                            print("⚠️ Skipping transaction with errors")
                            continue
                        
                        logs = data["params"]["result"]["value"].get("logs", [])
                        if any("InitializeMint" in log or "MintTo" in log for log in logs):
                            print("🚀 New token mint detected!")
                            
                            mint_info = await extract_mint_info(data)
                            if mint_info and not redis_client.sismember("processed_tokens", mint_info["mint_address"]):
                                redis_client.sadd("processed_tokens", mint_info["mint_address"])
                                print(f"✅ Token Added: {mint_info}")
                                await check_dex_screener(mint_info)

        except websockets.ConnectionClosedError:
            print("📡 Connection lost. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            await asyncio.sleep(5)

async def extract_mint_info(data):
    """Extracts the token mint address from transaction data"""
    try:
        # Get the logs from the transaction
        logs = data["params"]["result"]["value"].get("logs", [])
        
        # Get transaction details
        tx_details = data["params"]["result"]
        
        # Look for mint address in the instructions
        mint_address = None
        mint_authority = None
        
        # Parse through inner instructions to find mint operations
        if "meta" in tx_details and "innerInstructions" in tx_details["meta"]:
            for inner_ix in tx_details["meta"]["innerInstructions"]:
                for instruction in inner_ix["instructions"]:
                    if "parsed" in instruction and "type" in instruction["parsed"]:
                        if instruction["parsed"]["type"] in ["mintTo", "initializeMint"]:
                            mint_info = instruction["parsed"]["info"]
                            mint_address = mint_info.get("mint")
                            mint_authority = mint_info.get("mintAuthority")
                            break
                if mint_address:
                    break

        if mint_address:
            return {
                "mint_address": mint_address,
                "mint_authority": mint_authority or "Unknown",
                "mint_time": tx_details.get("blockTime", 0)
            }
        return None
        
    except Exception as e:
        print(f"❌ Error extracting mint info: {e}")
        return None

def fetch_dex_screener_tokens():
    """Fetches newly listed Solana tokens from DEX Screener API."""
    try:
        response = requests.get(DEX_SCREENER_URL)
        if response.status_code == 200:
            data = response.json()
            return data.get("pairs", [])
        return []
    except Exception as e:
        print(f"❌ Error fetching DEX Screener data: {e}")
        return []

async def check_dex_screener(mint_info):
    """Checks if a newly minted token is listed on DEX Screener."""
    while True:
        tokens = fetch_dex_screener_tokens()
        for pair in tokens:
            base_token = pair["baseToken"]
            if base_token["address"] == mint_info["mint_address"]:
                liquidity = pair["liquidity"]["usd"] if "liquidity" in pair else 0
                volume = pair["volume"]["h24"] if "volume" in pair else 0
                
                if liquidity >= 10000:  # Only track tokens with at least $10K liquidity
                    redis_client.sadd("listed_tokens", mint_info["mint_address"])
                    print(f"💰 Token Listed on DEX: {base_token['name']} ({base_token['symbol']})")
                    print(f"💰 Liquidity: ${liquidity:.2f}")
                    print(f"💰 Volume (24h): ${volume:.2f}")
                    print(f"🔗 DEX Screener URL: {pair['url']}")
                    return
        
        print("🔄 Checking DEX Screener again in 30s...")
        await asyncio.sleep(30)

async def main():
    await asyncio.gather(monitor_new_tokens())

if __name__ == "__main__":
    asyncio.run(main())
