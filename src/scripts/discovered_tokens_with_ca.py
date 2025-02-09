import pandas as pd
import requests
import time

def get_contract_address_from_coingecko(token_id: str, api_key: str) -> str:
    """Fetch the contract address of a token from CoinGecko."""
    url = f"https://api.coingecko.com/api/v3/coins/{token_id}"
    headers = {"x-cg-api-key": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            print("Rate limit hit! Sleeping for 60 seconds...")
            time.sleep(60)
            return get_contract_address_from_coingecko(token_id, api_key)
        
        response.raise_for_status()
        data = response.json()
        
        return data.get("platforms", {}).get("solana", "Not Found")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contract address for {token_id}: {e}")
        return "Not Found"

def update_discovered_tokens(file_path: str, api_key: str):
    """Read a CSV file, fetch contract addresses, and update the file."""
    df = pd.read_csv(file_path)
    
    if "contract_address" not in df.columns:
        df["contract_address"] = ""
    
    for index, row in df.iterrows():
        if not row["contract_address"] or row["contract_address"] == "Not Found":
            token_id = row["token_id"]
            contract_address = get_contract_address_from_coingecko(token_id, api_key)
            df.at[index, "contract_address"] = contract_address
            print(f"Updated {token_id}: {contract_address}")
    
    df.to_csv(file_path, index=False)
    print("✨ Updated file saved!")

# Example usage
API_KEY = "CG-1ngQzwMyki64dw9xpMvqu694"
FILE_PATH = "moondev/src/data/discovered_tokens_copy.csv"  # Path to your existing file
update_discovered_tokens(FILE_PATH, API_KEY)
