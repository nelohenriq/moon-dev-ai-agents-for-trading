"""
🌙 Moon Dev's Listing Arb System 🔍
Finds Solana tokens that aren't listed on major exchanges like Binance and Coinbase.
Runs every 24 hours to maintain an updated list.
"""

import os
import pandas as pd
import yfinance as yf
import time
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

# ⚙️ Configuration Constants
HOURS_BETWEEN_RUNS = 24
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
AI_ANALYSIS_FILE = Path("src/data/ai_analysis.csv")

# 📄 Predefined list of Solana tokens (add more as needed)
SOLANA_TOKENS = [
    'SOL-USD',  # Solana
    'SRM-USD',  # Serum
    'FTT-USD',  # FTX Token
    'RAY-USD',  # Raydium
    'STEP-USD', # Step Finance
    'MNGO-USD', # Mango Markets
    'ORCA-USD', # Orca
    'ATLAS-USD', # Star Atlas
    'POLIS-USD', # Star Atlas DAO
    'COPE-USD', # COPE
    'OXY-USD',  # Oxygen
    'MEDIA-USD', # Media Network
    'LIKE-USD', # Only1
    'SUNNY-USD', # Sunny Aggregator
    'SLND-USD', # Solend
    'PORT-USD', # Port Finance
    'SLRS-USD', # Solrise Finance
    'SNY-USD',  # Synthetify
    'MER-USD',  # Mercurial Finance
    'GRAPE-USD', # Grape Protocol
    'KIN-USD',  # Kin
    'SAMO-USD', # Samoyedcoin
    'WOOF-USD', # WOOF
    'SHDW-USD', # GenesysGo Shadow
    'mSOL-USD', # Marinade Staked SOL
    'scnSOL-USD', # Socean Staked SOL
]

class ListingArbSystem:
    """Utility class for finding promising Solana tokens 🦎"""
    
    def __init__(self):
        print("🦎 Moon Dev's Listing Arb System initialized!")
        
    def get_ohlcv_data(self, token_symbol: str) -> str:
        """Get OHLCV data for the past 14 days in 4-hour intervals using yfinance"""
        try:
            # Skip ignored tokens
            if token_symbol.lower() in DO_NOT_ANALYZE:
                print(f"⏭️ Skipping ignored token: {token_symbol}")
                return "❌ Token in ignore list"
            
            print(f"\n📈 Fetching OHLCV data for {token_symbol}...")
            
            # Fetch OHLCV data using yfinance
            ticker = yf.Ticker(token_symbol)
            
            # Calculate start and end dates for the past 14 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=14)
            
            # Fetch data with 4-hour intervals
            data = ticker.history(start=start_date, end=end_date, interval="4h")
            
            # Handle empty data
            if data.empty:
                print(f"⚠️ No OHLCV data returned for {token_symbol}")
                return "❌ No OHLCV data available (Empty Response)"
            
            # Format OHLCV data for AI analysis
            formatted_data = "📊 OHLCV Data (4h intervals, past 14 days):\n"
            formatted_data += "Timestamp | Open | High | Low | Close\n"
            formatted_data += "-" * 50 + "\n"
            
            # Process each OHLCV entry
            for index, row in data[-10:].iterrows():  # Show last 10 entries for readability
                timestamp = index.strftime('%Y-%m-%d %H:%M')
                open_price = f"${row['Open']:,.8f}"
                high = f"${row['High']:,.8f}"
                low = f"${row['Low']:,.8f}"
                close = f"${row['Close']:,.8f}"
                
                formatted_data += f"{timestamp} | {open_price} | {high} | {low} | {close}\n"
            
            # Add some basic statistics
            prices = data['Close'].values  # Close prices
            
            stats = f"""
            📈 Price Statistics:
            • Highest Price: ${np.max(prices):,.8f}
            • Lowest Price: ${np.min(prices):,.8f}
            • Average Price: ${np.mean(prices):,.8f}
            • Price Volatility: {np.std(prices)/np.mean(prices)*100:.2f}%
            
            📊 Trading Activity:
            • Number of Candles: {len(data)}
            • Latest Close: ${prices[-1]:,.8f}
            • Price Change: {((prices[-1]/prices[0])-1)*100:,.2f}% over period
            """
            
            # Print formatted data for verification
            print("\n📊 Formatted OHLCV Data:")
            print(formatted_data)
            print(stats)
            
            return formatted_data + stats
            
        except Exception as e:
            print(f"⚠️ Error fetching OHLCV data for {token_symbol}: {str(e)}")
            return "❌ No OHLCV data available (Network/API Error)"
        
    def analyze_token(self, token_symbol: str) -> dict:
        """Analyze a token using OHLCV data"""
        ohlcv_data = self.get_ohlcv_data(token_symbol)
        if not ohlcv_data:
            return None
        
        # Perform analysis (e.g., calculate average price, volume, etc.)
        avg_price = sum(ohlcv_data['close']) / len(ohlcv_data['close'])
        total_volume = ohlcv_data['volume']
        
        return {
            'symbol': token_symbol,
            'avg_price': avg_price,
            'total_volume': total_volume,
            'ohlcv_data': ohlcv_data,
        }
        
    def filter_tokens(self, tokens: List[str]) -> List[dict]:
        """Filter tokens based on criteria"""
        print("\n🔍 Starting token filtering process...")
        filtered_tokens = []
        
        for token in tokens:
            token_symbol = token.split('-')[0].lower()
            
            # Skip if in DO_NOT_ANALYZE list
            if token_symbol in DO_NOT_ANALYZE:
                print(f"\n⏭️ Skipping {token} - In DO_NOT_ANALYZE list")
                continue
            
            # Analyze token
            analysis = self.analyze_token(token)
            if not analysis:
                print(f"\n❌ Skipping {token} - Failed to fetch data")
                continue
            
            # Check volume requirement
            total_volume = analysis.get('total_volume', 0)
            if total_volume < MIN_VOLUME_USD:
                print(f"\n❌ Skipping {token} - Volume too low: ${total_volume:,.2f}")
                continue
            
            # Token passed all checks
            avg_price = analysis.get('avg_price', 0)
            print(f"\n✨ Found qualifying token: {token}")
            print(f"💰 Average Price: ${avg_price:,.8f}")
            print(f"📊 24h Volume: ${total_volume:,.2f}")
            
            filtered_tokens.append(analysis)
            
        print(f"\n🎯 Filtering complete!")
        print(f"✨ Found {len(filtered_tokens)} qualifying tokens")
        return filtered_tokens
        
    def save_analysis(self, analysis: List[dict]):
        """Save analysis results to CSV"""
        print("\n💾 Saving analysis results...")
        
        df = pd.DataFrame([{
            'symbol': token.get('symbol'),
            'avg_price': token.get('avg_price'),
            'total_volume': token.get('total_volume'),
            'analysis_time': datetime.now().isoformat()
        } for token in analysis])
        
        # Ensure directory exists
        AI_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(AI_ANALYSIS_FILE, index=False)
        print(f"✨ Saved {len(analysis)} analyses to {AI_ANALYSIS_FILE}")
        
    def load_discovered_tokens(self) -> List[str]:
        """Load previously discovered tokens"""
        if DISCOVERED_TOKENS_FILE.exists():
            df = pd.read_csv(DISCOVERED_TOKENS_FILE)
            print(f"\n📚 Loaded {len(df)} previously discovered tokens")
            return df['token_id'].tolist()
        return SOLANA_TOKENS  # Fallback to predefined list

def main():
    """Main function to run token discovery"""
    print("\n🌙 Moon Dev's Listing Arb System Starting Up! 🚀")
    print(f"📝 Results will be saved to: {AI_ANALYSIS_FILE.absolute()}")
    
    system = ListingArbSystem()
    
    try:
        while True:
            start_time = datetime.now()
            print(f"\n🔄 Starting new analysis round at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Load discovered tokens
            tokens = system.load_discovered_tokens()
            
            # Filter and analyze tokens
            filtered_tokens = system.filter_tokens(tokens)
            
            # Save results
            system.save_analysis(filtered_tokens)
            
            # Calculate next run time
            next_run = start_time.timestamp() + (HOURS_BETWEEN_RUNS * 3600)
            next_run_str = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n⏳ Next run in {HOURS_BETWEEN_RUNS} hours at {next_run_str}")
            print(f"💡 Press Ctrl+C to stop")
            
            # Sleep until next run
            time.sleep(HOURS_BETWEEN_RUNS * 3600)
            
    except KeyboardInterrupt:
        print("\n👋 Moon Dev's Listing Arb System signing off!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()