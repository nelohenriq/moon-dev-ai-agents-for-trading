import requests
import os
import time
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

RPC_ENDPOINT = os.getenv("RPC_ENDPOINT")


def get_transaction_detail(signature, max_retries=3):
    """
    Fetch transaction details with retry logic, including handling rate limit errors.

    Args:
        signature (str): The transaction signature.
        max_retries (int): Number of retry attempts.

    Returns:
        dict or None: Transaction details if successful, None otherwise.
    """
    tx_detail_payload = {
        "jsonrpc": "2.0",
        "id": "tx-detail",
        "method": "getTransaction",
        "params": [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "limit": 100}],
    }

    for attempt in range(max_retries):
        response = requests.post(RPC_ENDPOINT, json=tx_detail_payload).json()

        if "result" in response:
            return response["result"]

        if "error" in response:
            # If rate limit error is encountered, retry with backoff
            if response['error']['code'] == -32429:
                wait_time = 2 ** attempt  # Exponential backoff (1, 2, 4, 8, etc.)
                print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue  # Retry the request
            else:
                print(f"Error fetching transaction {signature}: {response['error']}")
                break  # Break the loop if it's not a rate limit error

    print(f"Failed to fetch details for transaction {signature} after {max_retries} attempts")
    return None


def get_sender_and_amount(tx_detail):
    try:
        # Extract sender from accountKeys (first signer)
        account_keys = tx_detail["transaction"]["message"]["accountKeys"]
        sender = None
        for key_info in account_keys:
            if key_info.get("signer", False):  # First signer is usually the sender
                sender = key_info["pubkey"]
                break
        print(f"Sender: {sender}")  # Debugging line

        # Extract amount from instructions
        amount = 0
        instructions = tx_detail["transaction"]["message"].get("instructions", [])
        for instruction in instructions:
            parsed_info = instruction.get("parsed", {}).get("info", {})
            if "source" in parsed_info and "lamports" in parsed_info:
                amount = int(parsed_info["lamports"]) / 1e9  # Convert lamports to SOL
                print(f"Amount: {amount}")  # Debugging line
                break  # Stop at first transfer

        return sender, amount

    except Exception as e:
        print(f"Error extracting sender and amount: {e}")

    return None, 0


def get_top_traders(token_address):
    """
    Identifies the top traders for a given token based on transaction volume.
    
    Args:
    - token_address (str): The token address to analyze.

    Returns:
    - list: Top 10 traders sorted by volume.
    """
    tx_payload = {
        "jsonrpc": "2.0",
        "id": "tx-history",
        "method": "getSignaturesForAddress",
        "params": [token_address, {"limit": 100}],
    }

    response = requests.post(RPC_ENDPOINT, json=tx_payload).json()
    if "result" not in response:
        print("Error fetching transaction history")
        return []

    wallet_volumes = {}
    for tx in response["result"]:
        tx_detail = get_transaction_detail(tx["signature"])
        if tx_detail:
            sender, amount = get_sender_and_amount(tx_detail)
            if sender:
                wallet_volumes[sender] = wallet_volumes.get(sender, 0) + amount

    return sorted(wallet_volumes.items(), key=lambda x: x[1], reverse=True)[:10]


def get_wallet_transactions(wallet_address):
    tx_payload = {
        "jsonrpc": "2.0",
        "id": "tx-history",
        "method": "getSignaturesForAddress",
        "params": [wallet_address, {"limit": 1000}],
    }

    response = requests.post(RPC_ENDPOINT, json=tx_payload).json()
    if "result" not in response:
        print("Error fetching transactions for wallet")
        return []

    transactions = []
    for tx in response["result"]:
        tx_detail = get_transaction_detail(tx["signature"])
        if tx_detail:
            # Look through instructions for token program transactions
            instructions = tx_detail.get("transaction", {}).get("message", {}).get("instructions", [])
            token_program_instructions = [
                ix for ix in instructions if ix.get("programId") == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss6Tq7dhtdTc"
            ]
            
            # If no token-related instructions found, skip this transaction
            if not token_program_instructions:
                print(f"Transaction {tx['signature']} does not contain token-related instructions.")
                continue

            # Print the instructions for debugging
            print(f"Transaction {tx['signature']} contains token-related instructions: {token_program_instructions}")
            
            # Check for token balances if token-related instructions exist
            post_balances = tx_detail.get("meta", {}).get("postTokenBalances", [])
            pre_balances = tx_detail.get("meta", {}).get("preTokenBalances", [])

            # Debugging: Check if the token balances are present
            if not post_balances and not pre_balances:
                print(f"Transaction {tx['signature']} has token-related instructions but no token balances.")
            
            # If both post and pre balances are empty, skip this transaction
            if not post_balances and not pre_balances:
                continue

            transactions.append({
                "signature": tx["signature"],
                "timestamp": tx_detail.get("blockTime"),
                "pre_balances": pre_balances,
                "post_balances": post_balances
            })

    return transactions

def calculate_roi(transaction):
    """
    Calculates the ROI from a transaction.

    Args:
    - transaction (dict): Transaction details.

    Returns:
    - float: ROI percentage.
    """
    post_balances = transaction.get("post_balances", [])
    
    if len(post_balances) >= 2:
        try:
            initial_balance = float(post_balances[0]["uiTokenAmount"]["amount"])
            final_balance = float(post_balances[-1]["uiTokenAmount"]["amount"])
            if initial_balance > 0:
                return ((final_balance - initial_balance) / initial_balance) * 100
        except Exception as e:
            print(f"Error calculating ROI: {e}")
    
    return 0


if __name__ == "__main__":
    # Load the CSV file into a DataFrame
    df = pd.read_csv("moondev/src/data/sniper_agent/recent_tokens.csv")

    # Reverse the order of rows
    df = df.iloc[::-1]

    for token_address in df["Token Address"]:

        top_traders = get_top_traders(token_address)
        print("Top Traders:", top_traders)

        if top_traders:
            wallet_tx = get_wallet_transactions(top_traders[0][0])
            #print("Wallet Transactions:", wallet_tx)

            if wallet_tx:
                roi = calculate_roi(wallet_tx[0])
                print("ROI:", roi)
