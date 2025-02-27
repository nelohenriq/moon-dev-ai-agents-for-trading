import websockets
import json
import datetime
import asyncio
import nest_asyncio
import json
from decimal import Decimal
from typing import Dict, List

# Constants for detection thresholds
LIQUIDITY_REMOVAL_THRESHOLD = Decimal('0.3')  # 30% of pool
LARGE_TRANSFER_THRESHOLD = Decimal('0.2')  # 20% of total supply
PRICE_IMPACT_THRESHOLD = Decimal('0.1')  # 10% price impact
SANDWICH_TIME_WINDOW = 3  # blocks
MEMPOOL_HISTORY: List[Dict] = []  # Store recent transactions

# Helius API endpoint
HELIUS_WS_URL = "wss://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"

async def check_for_rugpull_signals(tx_data: Dict) -> tuple[bool, list]:
    signals = []
    is_suspicious = False
    
    # Check for large liquidity removals
    if 'params' in tx_data and 'result' in tx_data['params']:
        logs = tx_data['params']['result']['value'].get('logs', [])
        
        for log in logs:
            # Check for Raydium/Orca liquidity removal
            if "RemoveLiquidity" in log or "WithdrawAllTokenTypes" in log:
                signals.append("Large liquidity removal detected")
                is_suspicious = True
            
            # Check for token burning
            if "Burn" in log:
                signals.append("Token burn detected")
                is_suspicious = True
                
            # Check for ownership transfers
            if "SetAuthority" in log or "TransferOwnership" in log:
                signals.append("Ownership transfer detected")
                is_suspicious = True
    
    # Check for massive token transfers
    if "Transfer" in str(tx_data):
        try:
            logs = tx_data['params']['result']['value'].get('logs', [])
            for log in logs:
                if "Transfer" in log:
                    signals.append("Large token transfer detected")
                    is_suspicious = True
        except (KeyError, AttributeError):
            pass

    return is_suspicious, signals


async def detect_frontrun_attempt(tx_data: Dict) -> tuple[bool, str]:
    global MEMPOOL_HISTORY
    signals = []
    
    # Add current transaction to history
    MEMPOOL_HISTORY.append({
        'timestamp': asyncio.get_event_loop().time(),
        'data': tx_data
    })
    
    # Clean old transactions
    current_time = asyncio.get_event_loop().time()
    MEMPOOL_HISTORY = [tx for tx in MEMPOOL_HISTORY 
                      if current_time - tx['timestamp'] < SANDWICH_TIME_WINDOW]
    
    # Check for sandwich patterns
    if len(MEMPOOL_HISTORY) >= 3:
        last_three = MEMPOOL_HISTORY[-3:]
        
        # Look for buy-sell-buy pattern with same token
        if ("Swap" in str(last_three[0]['data']) and 
            "Swap" in str(last_three[1]['data']) and 
            "Swap" in str(last_three[2]['data'])):
            
            signals.append("Potential sandwich attack pattern detected")
    
    # Check for high gas prices (priority fees)
    if 'params' in tx_data and 'result' in tx_data['params']:
        if tx_data['params'].get('priorityFeeLamports', 0) > 10000:
            signals.append("High priority fee detected")
    
    is_suspicious = len(signals) > 0
    return is_suspicious, " | ".join(signals)


async def extract_token_address(tx_data: Dict) -> str:
    if 'params' in tx_data and 'result' in tx_data['params']:
        logs = tx_data['params']['result']['value'].get('logs', [])
        
        for log in logs:
            if "InitializeMint" in log:
                # Extract token address from initialization log
                token_info = json.loads(log)
                return token_info.get('tokenAddress')
            
            if "MintTo" in log:
                # Extract from token creation event
                token_info = json.loads(log)
                return token_info.get('address')
    
    return None

async def process_transaction(message: str) -> Dict:
    tx_data = json.loads(message)
    token_address = await extract_token_address(tx_data)
    
    if token_address:
        print(f"🪙 New Token Detected: {token_address}")

    # Initialize default return structure
    result = {
        'transaction': tx_data,
        'security_checks': {
            'rug_pull': {
                'suspicious': False,
                'signals': []
            },
            'front_running': {
                'suspicious': False,
                'signals': []
            }
        }
    }
    
    # Run security checks
    rug_suspicious, rug_signals = await check_for_rugpull_signals(tx_data)
    front_suspicious, front_signals = await detect_frontrun_attempt(tx_data)

    # Update result with check findings
    result['security_checks']['rug_pull']['suspicious'] = rug_suspicious
    result['security_checks']['rug_pull']['signals'] = rug_signals
    result['security_checks']['front_running']['suspicious'] = front_suspicious
    result['security_checks']['front_running']['signals'] = front_signals
    
    if rug_suspicious:
        print(f"🚨 RUG PULL WARNING: {rug_signals}")
        print(f"Transaction: {tx_data.get('params', {}).get('result', {}).get('value', {}).get('signature', 'No signature')}")
    
    if front_suspicious:
        print(f"⚡ FRONT-RUNNING ALERT: {front_signals}")
        print(f"Transaction: {tx_data.get('params', {}).get('result', {}).get('value', {}).get('signature', 'No signature')}")
    
    return result

async def listen_helius():
    while True:  # Outer loop for reconnection
        try:
            async with websockets.connect(HELIUS_WS_URL) as ws:
                mint_subscription = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "logsSubscribe",
                    "params": [
                        {
                            "mentions": ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"]
                        }
                    ]
                }
                
                raydium_subscription = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "logsSubscribe",
                    "params": [
                        {
                            "mentions": ["675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"]
                        }
                    ]
                }

                await ws.send(json.dumps(mint_subscription))
                await ws.send(json.dumps(raydium_subscription))
                print("🔍 Monitoring for suspicious activities...")

                while True:  # Inner loop for messages
                    try:
                        message = await ws.recv()
                        analyzed_tx = await process_transaction(message)
                        #print(f"Processing transaction: {analyzed_tx}")
                    except websockets.ConnectionClosed:
                        print("Connection closed, reconnecting...")
                        break
                    except Exception as e:
                        print(f"Error processing transaction: {e}")
                        continue
                        
        except Exception as e:
            print(f"Connection error: {e}")
            await asyncio.sleep(5)  # Wait before reconnecting


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(listen_helius())
