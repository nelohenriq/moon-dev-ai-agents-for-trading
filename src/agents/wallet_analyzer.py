from src.agents.wallet_analyzer import get_top_traders
from src.agents.wallet_tracker import get_wallet_transactions, calculate_roi
import pandas as pd

def analyze_top_traders():
    # 1. Get high growth tokens
    growth_tokens = pd.read_csv("src/data/high_growth_tokens.csv")
    
    # 2. Get top traders for each token
    top_traders = {}
    for _, token in growth_tokens.iterrows():
        traders = get_top_traders(token['address'])
        for wallet, volume in traders:
            if wallet not in top_traders:
                top_traders[wallet] = {
                    'total_volume': 0,
                    'tokens_traded': [],
                    'success_rate': 0
                }
            top_traders[wallet]['total_volume'] += volume
            top_traders[wallet]['tokens_traded'].append(token['symbol'])
    
    # 3. Track these wallets' other trades
    for wallet in top_traders:
        all_trades = get_wallet_transactions(wallet)
        success_trades = [t for t in all_trades if calculate_roi(t) > 0]
        top_traders[wallet]['success_rate'] = len(success_trades) / len(all_trades)
    
    # 4. Save analysis
    df = pd.DataFrame(top_traders).T
    df.to_csv("src/data/top_traders_analysis.csv")
    
    return top_traders
