import requests
from src.agents.whales import check_lp_burn

# Replace with your actual Helius RPC URL and API key
HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key=cde2166e-a9cc-4f20-aab6-931319852b4a"
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"

def get_creator_tokens(creator_address):
    """Get all tokens created by address listed on Raydium with extended metrics"""
    
    # Define the payload to get assets by creator
    search_payload = {
        "jsonrpc": "2.0",
        "id": "creator-tokens",
        "method": "searchAssets",
        "params": {
            "authorityAddress": creator_address,
            "tokenType": "fungible",
            "page": 1,
            "limit": 100,
            "options": {
                "showNativeBalance": True,
                "showCollectionMetadata": True
            }
        }
    }

    # Make the request to Helius RPC
    response = requests.post(HELIUS_RPC_URL, headers={"Content-Type": "application/json"}, json=search_payload)
    
    if response.status_code == 200:
        try:
            data = response.json()

            # Check if there are tokens in the response
            if "result" in data and "items" in data["result"]:
                creator_tokens = []
                
                for item in data["result"]["items"]:
                    token_address = item["id"]

                    # Get token metadata including freeze authority
                    token_info_payload = {
                        "jsonrpc": "2.0",
                        "id": "token-info",
                        "method": "getAccountInfo",
                        "params": [token_address, {"encoding": "jsonParsed"}],
                    }

                    token_info = requests.post(
                        HELIUS_RPC_URL,
                        headers={"Content-Type": "application/json"},
                        json=token_info_payload,
                    ).json()

                    freeze_authority = token_info["result"]["value"]["data"]["parsed"]["info"].get(
                        "freezeAuthority"
                    )

                    mint_authority = token_info["result"]["value"]["data"]["parsed"]["info"].get(
                        "mintAuthority"
                    )

                    # Get top holders data
                    holders_payload = {
                        "jsonrpc": "2.0",
                        "id": "token-holders",
                        "method": "getProgramAccounts",
                        "params": [
                            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                            {
                                "filters": [
                                    {"dataSize": 165},
                                    {"memcmp": {"offset": 0, "bytes": token_address}},
                                ],
                                "encoding": "jsonParsed",
                            },
                        ],
                    }

                    holders = requests.post(
                        HELIUS_RPC_URL,
                        headers={"Content-Type": "application/json"},
                        json=holders_payload,
                    ).json()

                    # Calculate top holders percentage
                    total_supply = float(
                        token_info["result"]["value"]["data"]["parsed"]["info"]["supply"]
                    )
                    sorted_holders = sorted(
                        holders["result"],
                        key=lambda x: float(
                            x["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]
                        ),
                        reverse=True,
                    )
                    top_10_percentage = (
                        sum(
                            float(h["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
                            for h in sorted_holders[:10]
                        )
                        / total_supply
                        * 100
                    )

                    # Get DEX data including LP info
                    dex_data = requests.get(f"{DEXSCREENER_API}/{token_address}").json()

                    if "pairs" in dex_data:
                        raydium_pairs = [
                            pair for pair in dex_data["pairs"] if "raydium" in pair["dexId"].lower()
                        ]
                        if raydium_pairs:
                            # Check LP token burn
                            lp_address = raydium_pairs[0].get("pairAddress")
                            lp_burned = "Yes" if check_lp_burn(lp_address) else "No"

                            creator_tokens.append(
                                {
                                    "address": token_address,
                                    "name": dex_data["pairs"][0].get("baseToken", {}).get("name"),
                                    "symbol": dex_data["pairs"][0].get("baseToken", {}).get("symbol"),
                                    "price": dex_data["pairs"][0].get("priceUsd"),
                                    "liquidity": dex_data["pairs"][0].get("liquidity", {}).get("usd"),
                                    "volume_24h": dex_data["pairs"][0].get("volume", {}).get("h24"),
                                    "freeze_authority": freeze_authority,
                                    "mint_authority": mint_authority,
                                    "lp_burned": lp_burned,
                                    "top_10_holders_pct": top_10_percentage,
                                }
                            )

                return creator_tokens
        
        except Exception as e:
            print(f"Error occurred: {e}")
    
    # Return empty list if no data is found or if an error occurs
    return []

# Example creator address
creator_address = "06c5c1ce638d2567d26468b05eb951d1a28dcc6e123482b5c675149770e62bf2"
creator_tokens = get_creator_tokens(creator_address)
print(creator_tokens)
