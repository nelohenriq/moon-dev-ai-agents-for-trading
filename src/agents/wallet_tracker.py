import requests
import os
from dotenv import load_dotenv

load_dotenv()

RPC_ENDPOINT = os.getenv('RPC_ENDPOINT')

def get_top_traders(token_address):
    tx_payload = {
        "jsonrpc": "2.0",
        "id": "tx-history",
        "method": "getSignaturesForAddress",
        "params": [token_address, {"limit": 1000}]
    }
    
    response = requests.post(
        RPC_ENDPOINT,
        headers={"Content-Type": "application/json"},
        json=tx_payload
    ).json()
    
    wallet_volumes = {}
    for tx in response["result"]:
        # Get transaction details and sum up volumes
        tx_detail = get_transaction_detail(tx["signature"])
        wallet = tx_detail["from"]
        amount = tx_detail["amount"]
        wallet_volumes[wallet] = wallet_volumes.get(wallet, 0) + amount
        
    return sorted(wallet_volumes.items(), 
                 key=lambda x: x[1], 
                 reverse=True)[:10]

def get_transaction_detail(signature):
    tx_detail_payload = {
        "jsonrpc": "2.0",
        "id": "tx-detail",
        "method": "getTransaction",
        "params": [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
    }

    tx_detail = requests.post(
        RPC_ENDPOINT,
        headers={"Content-Type": "application/json"},
        json=tx_detail_payload,
    ).json()

    return tx_detail

def get_wallet_transactions(wallet_address):
    tx_payload = {
        "jsonrpc": "2.0",
        "id": "tx-history",
        "method": "getSignaturesForAddress",
        "params": [wallet_address, {"limit": 1000}]
    }

    tx_response = requests.post(
        RPC_ENDPOINT,
        headers={"Content-Type": "application/json"},
        json=tx_payload
    ).json()

    transactions = []
    for tx in tx_response["result"]:
        tx_detail = get_transaction_detail(tx["signature"])
        if tx_detail["result"]:
            transactions.append({
                "signature": tx["signature"],
                "timestamp": tx_detail["result"]["blockTime"],
                "type": "transfer",
                "post_balances": tx_detail["result"]["meta"]["postTokenBalances"]
            })
    return transactions

def calculate_roi(transaction):
    # Extract entry and exit prices from transaction data
    post_balances = transaction["post_balances"]
    if post_balances:
        initial_balance = float(post_balances[0]["uiTokenAmount"]["amount"])
        final_balance = float(post_balances[-1]["uiTokenAmount"]["amount"])
        roi = ((final_balance - initial_balance) / initial_balance) * 100 if initial_balance > 0 else 0
        return roi
    return 0
