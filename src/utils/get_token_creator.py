import requests
import time

DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"
TOKEN_ADDRESS = "BfuGKjyQMMJWVNPtdf1oTdenBsoJ6NMHEsVbzEo8B1oJ"
HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"

def get_token_creator(token_address):
    """Get token creator using Helius getAsset"""
    payload = {
        "jsonrpc": "2.0",
        "id": "token-info",
        "method": "getAsset",
        "params": {
            "id": token_address
        }
    }
    
    try:
        response = requests.post(
            HELIUS_RPC_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        ).json()

        if "result" in response and "creators" in response["result"]:
            return response["result"]["creators"]
        return "Creator not found"
        
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        time.sleep(2)  # Simple retry delay on error
        return get_token_creator(token_address)  # Retry the request
        
    return None

token_creator = get_token_creator(TOKEN_ADDRESS)
print(token_creator)