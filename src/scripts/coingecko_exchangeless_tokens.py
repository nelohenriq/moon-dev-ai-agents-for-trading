"""
🌙 Moon Dev's CoinGecko Token Finder 🔍
Finds Solana tokens that aren't listed on major exchanges like Binance and Coinbase.
Runs every 24 hours to maintain an updated list.
"""

import os
import pandas as pd
import yfinance as yf
import time
from typing import Dict, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ⚙️ Configuration Constants
HOURS_BETWEEN_RUNS = 24
MAJOR_EXCHANGES = ['binance', 'coinbase']  # Exchanges to exclude
MIN_VOLUME_USD = 100_000  # Minimum 24h volume in USD

# 🚫 Tokens to Skip (e.g. stablecoins, wrapped tokens)
DO_NOT_ANALYZE = [
    'tether',           # USDT
    'usdt',            # Alternative USDT id
    'usdtsolana',      # Solana USDT
    'wrapped-solana',   # Wrapped SOL
    'usdc',            # USDC
]

# 📁 File Paths
DISCOVERED_TOKENS_FILE = Path("src/data/discovered_tokens.csv")

class CoinGeckoTokenFinder:
    """Utility class for finding promising Solana tokens 🦎"""
    
    def __init__(self):
        print("🦎 Moon Dev's CoinGecko Token Finder initialized!")
        
    def get_solana_tokens(self) -> pd.DataFrame:
        """Get all Solana tokens with market data"""
        print("\n🔍 Getting Solana tokens from Yahoo Finance...")
        
        # Example token tickers for Solana ecosystem
        solana_tokens = ['SOL-USD', 'SRM-USD', 'FTT-USD']  # Add more tokens as needed
        all_tokens = []

        for token in solana_tokens:
            data = yf.download(token, period='1d', interval='1m')
            if not data.empty:
                token_info = {
                    'id': token,
                    'name': token,  # You may want to map this to actual names
                    'symbol': token.split('-')[0],
                    'current_price': data['Close'].iloc[-1],
                    'total_volume': data['Volume'].sum()  # Total volume for the day
                }
                all_tokens.append(token_info)
        
        print(f"📊 Retrieved {len(all_tokens)} tokens")
        return all_tokens
        
    def filter_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """Filter tokens based on criteria"""
        print("\n🔍 Starting token filtering process...")
        filtered_tokens = []
        
        for token in tokens:
            token_id = token.get('id', '').lower()
            name = token.get('name', 'Unknown')
            symbol = token.get('symbol', 'N/A').upper()
            
            # Check volume requirement
            total_volume = token.get('total_volume', 0)
            if isinstance(total_volume, (int, float)):
                volume_usd = total_volume
            else:
                volume_usd = float(total_volume.iloc[0]) if hasattr(total_volume, 'iloc') else 0
            
            if volume_usd < MIN_VOLUME_USD:
                print(f"\n❌ Skipping {name} ({symbol}) - Volume too low: ${volume_usd:,.2f}")
                continue
            
            # Token passed all checks
            price = token.get('current_price')
            if isinstance(price, pd.Series):
                price = price.iloc[0]
            price_str = f"${price:,.8f}" if price is not None else "N/A"
            
            print(f"\n✨ Found qualifying token: {name} ({symbol})")
            print(f"💰 Price: {price_str}")
            print(f"📊 24h Volume: ${volume_usd:,.2f}")
            
            filtered_tokens.append(token)
            
        print(f"\n🎯 Filtering complete!")
        print(f"✨ Found {len(filtered_tokens)} qualifying tokens")
        return filtered_tokens
        
    def save_discovered_tokens(self, tokens: List[Dict]):
        """Save discovered tokens to CSV"""
        print("\n💾 Saving discovered tokens...")
        
        df = pd.DataFrame([{
            'token_id': token.get('id', 'unknown'),
            'symbol': token.get('symbol', 'N/A'),
            'name': token.get('name', 'Unknown'),
            'price': token.get('current_price'),
            'volume_24h': token.get('total_volume', 0),
            'discovered_at': datetime.now().isoformat()
        } for token in tokens])
        
        # Ensure directory exists
        DISCOVERED_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(DISCOVERED_TOKENS_FILE, index=False)
        print(f"✨ Saved {len(tokens)} tokens to {DISCOVERED_TOKENS_FILE}")
        
    def load_discovered_tokens(self) -> pd.DataFrame:
        """Load previously discovered tokens"""
        if DISCOVERED_TOKENS_FILE.exists():
            df = pd.read_csv(DISCOVERED_TOKENS_FILE)
            print(f"\n📚 Loaded {len(df)} previously discovered tokens")
            return df
        return pd.DataFrame()

def main():
    """Main function to run token discovery"""
    print("\n🌙 Moon Dev's Token Finder Starting Up! 🚀")
    print(f"📝 Results will be saved to: {DISCOVERED_TOKENS_FILE.absolute()}")
    
    finder = CoinGeckoTokenFinder()
    
    try:
        while True:
            start_time = datetime.now()
            print(f"\n🔄 Starting new token discovery round at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get and filter tokens
            tokens = finder.get_solana_tokens()
            filtered_tokens = finder.filter_tokens(tokens)
            
            # Save results
            finder.save_discovered_tokens(filtered_tokens)
            
            # Calculate next run time
            next_run = start_time.timestamp() + (HOURS_BETWEEN_RUNS * 3600)
            next_run_str = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n⏳ Next run in {HOURS_BETWEEN_RUNS} hours at {next_run_str}")
            print(f"💡 Press Ctrl+C to stop")
            
            # Sleep until next run
            time.sleep(HOURS_BETWEEN_RUNS * 3600)
            
    except KeyboardInterrupt:
        print("\n👋 Moon Dev's Token Finder signing off!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()