from src.agents.pool_scanner import discover_raydium_pools
from src.agents.market_scanner import get_high_growth_tokens
import pandas as pd

def analyze_market_opportunities():
    # Get high growth tokens
    growth_tokens = get_high_growth_tokens()
    
    # Get Raydium pools
    raydium_pools = discover_raydium_pools()
    
    # Merge and analyze
    market_data = []
    for token in growth_tokens:
        matching_pools = [p for p in raydium_pools if p["token_address"] == token["address"]]
        
        if matching_pools:
            pool = matching_pools[0]
            market_data.append({
                "token_address": token["address"],
                "symbol": token["symbol"],
                "market_cap": token["market_cap"],
                "age_days": token["age_days"],
                "pool_liquidity": pool["liquidity_usd"],
                "pool_volume_24h": pool["volume_24h"],
                "pool_creation": pool["creation_time"],
                "growth_velocity": token["market_cap"] / token["age_days"]
            })
    
    # Save comprehensive analysis
    df = pd.DataFrame(market_data)
    df.to_csv("src/data/market_intelligence.csv", index=False)
    
    return market_data
