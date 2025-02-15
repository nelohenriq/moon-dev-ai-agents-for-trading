import requests
from datetime import datetime
import pandas as pd
import os

DEXSCREENER_API = os.getenv("DEXSCREENER_API")

def discover_raydium_pools():
    dex_data = requests.get(f"{DEXSCREENER_API}/pairs").json()
    raydium_pools = []
    
    for pair in dex_data["pairs"]:
        if "raydium" in pair["dexId"].lower():
            pool_data = {
                "pair_address": pair["pairAddress"],
                "token_address": pair["baseToken"]["address"],
                "symbol": pair["baseToken"]["symbol"],
                "liquidity_usd": pair.get("liquidity", {}).get("usd", 0),
                "creation_time": datetime.fromtimestamp(pair.get("pairCreatedAt", 0)),
                "volume_24h": pair.get("volume", {}).get("h24", 0)
            }
            raydium_pools.append(pool_data)
    
    df = pd.DataFrame(raydium_pools)
    df.to_csv("src/data/raydium_pools.csv", index=False)
    
    return raydium_pools
