import requests

HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"


def get_top_transactions(mint_address, limit=10):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [mint_address, {"limit": limit}]
    }
    response = requests.post(HELIUS_RPC_URL, json=payload)
    transactions = response.json().get('result', [])
    
    top_transactions = []
    for tx in transactions:
        signature = tx['signature']
        tx_details = get_transaction_details(signature)
        if 'result' in tx_details and tx_details['result']:
            transaction = tx_details['result']
            # Extract sender and receiver addresses from the transaction details
            # This depends on the specific structure of the transaction
            # For example, you might need to parse the 'transaction' field
            # to find the relevant accounts involved in the transfer
            # Add the sender and receiver addresses to the top_transactions list
            # top_transactions.append((sender_address, receiver_address))
    
    return top_transactions

def get_transaction_details(signature):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"maxSupportedTransactionVersion": 0}]
    }
    response = requests.post(HELIUS_RPC_URL, json=payload)
    print(response.json())
    return response.json()

# Example usage
mint_address = 'y7ZPxJHfTxiTPZMM9v5FXH1J8z19XTupDK5eVVGj6Ld'
top_transactions = get_top_transactions(mint_address)
print(top_transactions)