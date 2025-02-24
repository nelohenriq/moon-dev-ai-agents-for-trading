import requests

HELIUS_RPC_URL = (
    "https://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"
)


def get_top_transactions(mint_address, limit=10):
    """
    Fetches the top transactions for a given mint address and extracts sender and receiver addresses.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [mint_address, {"limit": limit, "encoding": "jsonParsed"}],
    }
    response = requests.post(HELIUS_RPC_URL, json=payload)
    transactions = response.json().get("result", [])

    top_transactions = []
    for tx in transactions:
        signature = tx["signature"]
        tx_details = get_transaction_details(signature)

        if "result" in tx_details and tx_details["result"]:
            transaction = tx_details["result"]
            instructions = (
                transaction.get("transaction", {})
                .get("message", {})
                .get("instructions", [])
            )

            sender = None
            receiver = None

            for instruction in instructions:
                if (
                    instruction.get("programId")
                    == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                ):
                    accounts = instruction.get("accounts", [])
                    if len(accounts) >= 2:
                        sender = accounts[0]  # Usually, first account is sender
                        receiver = accounts[1]  # Second account is receiver
                        break  # Extract first valid transfer

            if sender and receiver:
                top_transactions.append((signature, sender, receiver))

    return top_transactions


def get_transaction_details(signature):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            signature,
            {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"},
        ],
    }
    response = requests.post(HELIUS_RPC_URL, json=payload)
    from pprint import pprint

    pprint(response.json())
    return response.json()


# Example usage
mint_address = "y7ZPxJHfTxiTPZMM9v5FXH1J8z19XTupDK5eVVGj6Ld"
top_transactions = get_top_transactions(mint_address)
print("Top transcations: ", top_transactions)
