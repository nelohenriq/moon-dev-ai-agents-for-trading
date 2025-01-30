"""
🌙 Moon Dev's Listing Arb System 🔍
Finds Solana tokens that aren't listed on major exchanges like Binance and Coinbase.
Runs every 24 hours to maintain an updated list.
"""

import os
import pandas as pd
import time
import openai
import numpy as np
import json
import yfinance as yf
import time
import openai
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from typing import List
import concurrent.futures
from datetime import datetime, timedelta
from collections import deque
from termcolor import colored, cprint
from typing import Dict
import requests


class RateLimiter:
    def __init__(self, max_requests=30, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = deque()

    def wait_if_needed(self):
        now = datetime.now()
        
        # Remove requests older than time window
        while self.requests and (now - self.requests[0]).total_seconds() > self.time_window:
            self.requests.popleft()
            
        # If at rate limit, wait until oldest request expires
        if len(self.requests) >= self.max_requests:
            wait_time = self.time_window - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                print(f"🕐 Rate limit reached, waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                
        self.requests.append(now)

# Load environment variables
load_dotenv()

# ⚙️ Configuration
HOURS_BETWEEN_RUNS = 24        # Run AI analysis every 24 hours to manage API costs
PARALLEL_PROCESSES = 50        # Number of parallel processes to run
MIN_VOLUME_USD = 100_000      # Minimum 24h volume to analyze
MAX_MARKET_CAP = 10_000_000   # Maximum market cap to include in analysis (10M)

# 🚫 Tokens to Skip (e.g. stablecoins, wrapped tokens)
DO_NOT_ANALYZE = [
    'tether',           # USDT - Stablecoin
    'usdt',            # Alternative USDT id
    'usdtsolana',      # Solana USDT
    'usdc',            # USDC
    'usd-coin',        # Alternative USDC id
    'busd',            # Binance USD
    'dai',             # DAI
    'frax',            # FRAX
    'true-usd',        # TUSD
    'wrapped-bitcoin',  # WBTC
    'wrapped-solana',  # WSOL
]

# 📁 File Paths
DISCOVERED_TOKENS_FILE = Path("src/data/discovered_tokens.csv")
AI_ANALYSIS_FILE = Path("src/data/ai_analysis.csv")

# 🤖 CoinGecko API Settings
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
TEMP_DATA_DIR = Path("src/data/temp_data")

# 🤖 Agent Model Selection
AGENT_ONE_MODEL = "deepseek-r1:7b"     # Technical Analysis Agent
AGENT_TWO_MODEL = "deepseek-r1:7b"    # Fundamental Analysis Agent

# 🤖 Agent Prompts
AGENT_ONE_PROMPT = """
You are the Technical Analysis Agent 📊
Your role is to analyze token metrics, market data, and OHLCV patterns.

IMPORTANT: Start your response with one of these recommendations:
RECOMMENDATION: BUY
RECOMMENDATION: SELL
RECOMMENDATION: DO NOTHING

Then provide your detailed analysis.

Focus on:
- Volume trends and liquidity patterns
- Price action and momentum using OHLCV data
- Support and resistance levels from price history
- Market cap relative to competitors
- Technical indicators and patterns
- 4-hour chart analysis for the past 14 days

Help Moon Dev identify tokens with strong technical setups! 🎯
"""

AGENT_TWO_PROMPT = """
You are the Fundamental Analysis Agent 🔬
Your role is to analyze project fundamentals and potential.

IMPORTANT: Start your response with one of these recommendations:
RECOMMENDATION: BUY
RECOMMENDATION: SELL
RECOMMENDATION: DO NOTHING

Then provide your detailed analysis.

Focus on:
- Project technology and innovation
- Team background and development activity
- Community growth and engagement
- Competition and market positioning
- Growth potential and risks
- How the technical analysis aligns with fundamentals

Help Moon Dev evaluate which tokens have the best fundamentals! 🚀
"""

class AIAgent:
    """AI Agent for analyzing tokens using Ollama via OpenAI client"""
    
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model  # e.g., "llama2", "mistral"
        self.client = openai.OpenAI(
            base_url="http://localhost:11434/v1",  # Ollama's OpenAI-compatible endpoint
            api_key="ollama"  # API key is not required for Ollama
        )
        self.memory_file = Path(f"src/data/agent_memory/{name.lower().replace(' ', '_')}.json")
        self.memory = {
            'analyzed_tokens': [],
            'promising_tokens': [],
            'conversations': []
        }
        self.load_memory()
        cprint(f"🤖 {name} initialized with {model}!", "white", "on_green")
        
    def load_memory(self):
        """Load agent memory"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    try:
                        loaded_memory = json.load(f)
                        # Ensure all required keys exist
                        for key in ['analyzed_tokens', 'promising_tokens', 'conversations']:
                            if key not in loaded_memory:
                                loaded_memory[key] = []
                        self.memory = loaded_memory
                        print(f"📚 Loaded {len(self.memory['conversations'])} previous conversations for {self.name}")
                    except json.JSONDecodeError:
                        print(f"⚠️ Warning: Corrupted memory file for {self.name}, using empty memory")
            else:
                print(f"📝 Created new memory file for {self.name}")
                self.memory_file.parent.mkdir(parents=True, exist_ok=True)
                self.save_memory()
        except Exception as e:
            print(f"⚠️ Error loading memory for {self.name}: {str(e)}")
            
    def save_memory(self):
        """Save agent memory"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
            
    def analyze(self, token_data: Dict, other_agent_analysis: str = None) -> str:
        """Analyze a token using Ollama via OpenAI client"""
        try:
            # Format token data for analysis
            token_info = f"""
🪙 Token Information:
• Name: {token_data['name']} ({token_data['symbol']})
• Token ID: {token_data['token_id']}
• Current Price: ${float(token_data.get('price', 0)):,.8f}
• 24h Volume: ${float(token_data.get('volume_24h', 0)):,.2f}
• Market Cap: ${float(token_data.get('market_cap', 0)):,.2f}

{token_data.get('ohlcv_data', '❌ No OHLCV data available')}
"""
            
            # Build the prompt
            if self.name == "Agent One":
                system_prompt = AGENT_ONE_PROMPT
                user_prompt = f"""Please analyze this token's technical metrics and OHLCV data:

{token_info}

Focus on:
1. Price action patterns in the 4h chart
2. Volume trends and anomalies
3. Support/resistance levels
4. Technical indicators from the OHLCV data
5. Potential entry/exit points based on the data

Remember to reference specific data points from the OHLCV table in your analysis!"""
            else:
                system_prompt = AGENT_TWO_PROMPT
                user_prompt = f"""Please analyze this token considering the technical analysis and OHLCV data:

{token_info}

Agent One's Technical Analysis:
{other_agent_analysis}

Focus on:
1. How the OHLCV data supports or contradicts the fundamentals
2. Volume patterns that indicate growing/declining interest
3. Price stability and growth potential
4. Market positioning based on the data
5. Risk assessment using both technical and fundamental factors

Remember to reference specific data points from the OHLCV table in your analysis!"""
            
            # Get AI response using OpenAI client
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            analysis = response.choices[0].message.content
            
            # Update memory
            self.memory['analyzed_tokens'].append({
                'token_id': token_data['token_id'],
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'had_ohlcv_data': 'ohlcv_data' in token_data
            })
            
            self.memory['conversations'].append({
                'timestamp': datetime.now().isoformat(),
                'token': token_data['token_id'],
                'prompt': user_prompt,
                'response': analysis,
                'included_ohlcv': 'ohlcv_data' in token_data
            })
            
            self.save_memory()
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Error in {self.name}'s analysis: {str(e)}")
            return f"Error analyzing token: {str(e)}"

# The rest of the code (ListingArbSystem class and main function) remains unchanged.
# Just replace the AIAgent initialization in ListingArbSystem with the new Ollama-based AIAgent.

class ListingArbSystem:
    """AI Agent system for analyzing potential listing opportunities"""
    
    def __init__(self):
        self.agent_one = AIAgent("Agent One", AGENT_ONE_MODEL)
        self.agent_two = AIAgent("Agent Two", AGENT_TWO_MODEL)
        self.analysis_log = self._load_analysis_log()
        cprint("🔍 Moon Dev's Listing Arb System Ready!", "white", "on_green", attrs=["bold"])
        
    def _load_analysis_log(self) -> pd.DataFrame:
        """Load or create AI analysis log"""
        if AI_ANALYSIS_FILE.exists():
            df = pd.read_csv(AI_ANALYSIS_FILE)
            print(f"\n📈 Loaded analysis log with {len(df)} previous analyses")
            return df
        else:
            df = pd.DataFrame(columns=[
                'timestamp', 
                'token_id', 
                'symbol', 
                'name',
                'price', 
                'volume_24h', 
                'market_cap',
                'agent_one_recommendation', 
                'agent_two_recommendation'
            ])
            df.to_csv(AI_ANALYSIS_FILE, index=False)
            print("\n📝 Created new analysis log")
            return df
            
    def load_discovered_tokens(self) -> pd.DataFrame:
        """Load tokens from discovery script"""
        if not DISCOVERED_TOKENS_FILE.exists():
            raise FileNotFoundError(f"❌ No discovered tokens file found at {DISCOVERED_TOKENS_FILE}")
            
        df = pd.read_csv(DISCOVERED_TOKENS_FILE)
        print(f"\n📚 Loaded {len(df)} tokens from {DISCOVERED_TOKENS_FILE}")
        return df
        
    def get_ohlcv_data(self, token_id: str) -> str:
        """Get OHLCV data for the past 14 days in 4-hour intervals"""
        try:
            # Skip ignored tokens
            if token_id.lower() in DO_NOT_ANALYZE:
                print(f"⏭️ Skipping ignored token: {token_id}")
                return "❌ Token in ignore list"
            
            print(f"\n📈 Fetching OHLCV data for {token_id}...")
            
            url = f"{COINGECKO_BASE_URL}/coins/{token_id}/ohlc"
            params = {
                'vs_currency': 'usd',  # Required parameter
                'days': '14'           # Will give us 4h intervals based on docs
            }
            headers = {
                'x-cg-pro-api-key': COINGECKO_API_KEY
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            # Print raw response for debugging
            print("\n🔍 Raw API Response:")
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Data: {response.text[:500]}...")  # First 500 chars
            
            # Handle API errors gracefully
            if response.status_code != 200:
                print(f"⚠️ API returned status code {response.status_code} for {token_id}")
                return f"❌ No OHLCV data available (API Error: {response.status_code})"
            
            ohlcv_data = response.json()
            
            if not ohlcv_data or len(ohlcv_data) < 2:  # Need at least 2 data points
                print(f"⚠️ No OHLCV data returned for {token_id}")
                return "❌ No OHLCV data available (Empty Response)"
            
            # Format OHLCV data for AI analysis
            formatted_data = "📊 OHLCV Data (4h intervals, past 14 days):\n"
            formatted_data += "Timestamp | Open | High | Low | Close\n"
            formatted_data += "-" * 50 + "\n"
            
            try:
                # Process each OHLCV entry
                # OHLCV format from API: [timestamp, open, high, low, close]
                for entry in ohlcv_data[-10:]:  # Show last 10 entries for readability
                    timestamp = datetime.fromtimestamp(entry[0]/1000).strftime('%Y-%m-%d %H:%M')
                    open_price = f"${entry[1]:,.8f}"
                    high = f"${entry[2]:,.8f}"
                    low = f"${entry[3]:,.8f}"
                    close = f"${entry[4]:,.8f}"
                    
                    formatted_data += f"{timestamp} | {open_price} | {high} | {low} | {close}\n"
                
                # Add some basic statistics
                prices = np.array([float(entry[4]) for entry in ohlcv_data])  # Close prices
                
                stats = f"""
                📈 Price Statistics:
                • Highest Price: ${np.max(prices):,.8f}
                • Lowest Price: ${np.min(prices):,.8f}
                • Average Price: ${np.mean(prices):,.8f}
                • Price Volatility: {np.std(prices)/np.mean(prices)*100:.2f}%
                
                📊 Trading Activity:
                • Number of Candles: {len(ohlcv_data)}
                • Latest Close: ${prices[-1]:,.8f}
                • Price Change: {((prices[-1]/prices[0])-1)*100:,.2f}% over period
                """
                
                # Print formatted data for verification
                print("\n📊 Formatted OHLCV Data:")
                print(formatted_data)
                print(stats)
                
                return formatted_data + stats
                
            except (IndexError, TypeError, ValueError) as e:
                print(f"⚠️ Error processing OHLCV data for {token_id}: {str(e)}")
                return "❌ No OHLCV data available (Data Processing Error)"
                
        except Exception as e:
            print(f"⚠️ Error fetching OHLCV data for {token_id}: {str(e)}")
            return "❌ No OHLCV data available (Network/API Error)"

    def _should_analyze_token(self, token_id: str) -> bool:
        """Check if token needs analysis based on last analysis time"""
        if not self.analysis_log.empty:
            last_analysis = self.analysis_log[self.analysis_log['token_id'] == token_id]
            if not last_analysis.empty:
                last_time = pd.to_datetime(last_analysis['timestamp'].iloc[-1])
                hours_since = (datetime.now() - last_time).total_seconds() / 3600
                if hours_since < HOURS_BETWEEN_RUNS:
                    print(f"⏭️ Skipping {token_id} - Analyzed {hours_since:.1f} hours ago")
                    return False
        return True

    def analyze_tokens_parallel(self, tokens_batch):
        """Analyze a batch of tokens in parallel"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_PROCESSES) as executor:
            # Create a list of tokens that need analysis
            tokens_to_analyze = []
            for _, token_data in tokens_batch.iterrows():
                if self._should_analyze_token(token_data['token_id']):
                    tokens_to_analyze.append(token_data.to_dict())
            
            if tokens_to_analyze:
                # Submit all tokens for analysis
                futures = [executor.submit(self.analyze_token, token) for token in tokens_to_analyze]
                # Wait for all to complete
                concurrent.futures.wait(futures)
            
            print(f"✅ Batch complete - Analyzed {len(tokens_to_analyze)} tokens")

    def analyze_token(self, token_data: Dict):
        """Have both agents analyze a token"""
        try:
            name = token_data.get('name', 'Unknown')
            symbol = token_data.get('symbol', 'UNKNOWN')
            token_id = token_data.get('token_id', '')
            
            try:
                volume = float(token_data.get('volume_24h', 0))
                price = float(token_data.get('price', 0))
                market_cap = float(token_data.get('market_cap', 0))
            except (TypeError, ValueError):
                volume = 0
                price = 0
                market_cap = 0
                
            print(f"\n🔍 Analyzing: {name} ({symbol})")
            print(f"📊 24h Volume: ${volume:,.2f}")
            print(f"💰 Market Cap: ${market_cap:,.2f}")
            
            # Skip if market cap too high (check this first)
            if market_cap > MAX_MARKET_CAP:
                print(f"⏭️ Skipping - Market cap above maximum (${MAX_MARKET_CAP:,.0f})")
                return
            
            # Skip if volume too low
            if volume < MIN_VOLUME_USD:
                print(f"⏭️ Skipping - Volume below minimum (${MIN_VOLUME_USD:,.2f})")
                return
            
            # Get OHLCV data
            ohlcv_data = self.get_ohlcv_data(token_id)
            
            # Skip if OHLCV data fetch failed
            if ohlcv_data.startswith("❌"):
                print(f"⏭️ Skipping - Failed to get OHLCV data")
                return
            
            # Add OHLCV data to token_data for analysis
            analysis_data = token_data.copy()
            analysis_data['ohlcv_data'] = ohlcv_data
            
            # Ensure all required fields exist with defaults
            for field in ['price', 'market_cap']:
                if field not in analysis_data:
                    analysis_data[field] = 0
                
            # Agent One analyzes first
            agent_one_analysis = self.agent_one.analyze(analysis_data)
            if agent_one_analysis.startswith("Error analyzing token"):
                print("⚠️ Agent One analysis failed, skipping token")
                return
            
            # Extract Agent One's recommendation
            agent_one_rec = "DO NOTHING"  # Default
            if "RECOMMENDATION:" in agent_one_analysis:
                rec_line = agent_one_analysis.split("\n")[0]
                if "BUY" in rec_line:
                    agent_one_rec = "BUY"
                elif "SELL" in rec_line:
                    agent_one_rec = "SELL"
            
            print("\n🤖 Agent One Analysis:")
            cprint(agent_one_analysis, "white", "on_green")
            
            # Agent Two responds
            agent_two_analysis = self.agent_two.analyze(analysis_data, agent_one_analysis)
            if agent_two_analysis.startswith("Error analyzing token"):
                print("⚠️ Agent Two analysis failed, skipping token")
                return
            
            # Extract Agent Two's recommendation
            agent_two_rec = "DO NOTHING"  # Default
            if "RECOMMENDATION:" in agent_two_analysis:
                rec_line = agent_two_analysis.split("\n")[0]
                if "BUY" in rec_line:
                    agent_two_rec = "BUY"
                elif "SELL" in rec_line:
                    agent_two_rec = "SELL"
            
            print("\n🤖 Agent Two Analysis:")
            cprint(agent_two_analysis, "white", "on_green")
            
            # Save analysis to log
            try:
                self.analysis_log = pd.concat([
                    self.analysis_log,
                    pd.DataFrame([{
                        'timestamp': datetime.now().isoformat(),
                        'token_id': token_id,
                        'symbol': symbol,
                        'name': name,
                        'price': price,
                        'volume_24h': volume,
                        'market_cap': analysis_data.get('market_cap', 0),
                        'agent_one_recommendation': agent_one_rec,
                        'agent_two_recommendation': agent_two_rec,
                        'coingecko_url': f"https://www.coingecko.com/en/coins/{token_id}"
                    }])
                ], ignore_index=True)
                
                # Save to CSV
                self.analysis_log.to_csv(AI_ANALYSIS_FILE, index=False)
                print(f"\n💾 Analysis saved to {AI_ANALYSIS_FILE}")
                print(f"📊 Recommendations: Agent One: {agent_one_rec} | Agent Two: {agent_two_rec}")
                print(f"🔗 CoinGecko URL: https://www.coingecko.com/en/coins/{token_id}")
                
            except Exception as e:
                print(f"⚠️ Error saving analysis: {str(e)}")
            
        except Exception as e:
            print(f"⚠️ Error analyzing {token_data.get('name', 'Unknown')}: {str(e)}")
            
    def run_analysis_cycle(self):
        """Run one complete analysis cycle with parallel processing"""
        try:
            print("\n🔄 Starting New Analysis Round!")
            
            # Load discovered tokens
            discovered_tokens_df = self.load_discovered_tokens()
            
            # Sort by volume for efficiency
            discovered_tokens_df = discovered_tokens_df.sort_values('volume_24h', ascending=False)
            
            # Split into batches for parallel processing
            batch_size = max(1, len(discovered_tokens_df) // PARALLEL_PROCESSES)
            batches = [discovered_tokens_df[i:i + batch_size] for i in range(0, len(discovered_tokens_df), batch_size)]
            
            print(f"\n📊 Processing {len(discovered_tokens_df)} tokens in {len(batches)} batches")
            print(f"⚡ Using {PARALLEL_PROCESSES} parallel processes")
            print(f"⏰ Minimum {HOURS_BETWEEN_RUNS} hours between token analysis")
            
            # Process each batch
            for i, batch in enumerate(batches, 1):
                print(f"\n🔄 Processing batch {i}/{len(batches)} ({len(batch)} tokens)")
                self.analyze_tokens_parallel(batch)
                
            # After completing the analysis, create filtered buy recommendations
            if AI_ANALYSIS_FILE.exists():
                # Read the full analysis file
                full_analysis = pd.read_csv(AI_ANALYSIS_FILE)
                
                # Safety check: Ensure all entries have CoinGecko URLs
                print("\n🔍 Checking for missing CoinGecko URLs...")
                if 'coingecko_url' not in full_analysis.columns:
                    print("➕ Adding CoinGecko URL column")
                    full_analysis['coingecko_url'] = full_analysis['token_id'].apply(
                        lambda x: f"https://www.coingecko.com/en/coins/{x}"
                    )
                else:
                    # Fill in any missing URLs
                    missing_urls = full_analysis['coingecko_url'].isna()
                    if missing_urls.any():
                        print(f"🔗 Adding missing URLs for {missing_urls.sum()} entries")
                        full_analysis.loc[missing_urls, 'coingecko_url'] = full_analysis.loc[missing_urls, 'token_id'].apply(
                            lambda x: f"https://www.coingecko.com/en/coins/{x}"
                        )
                
                # Save the updated full analysis
                full_analysis.to_csv(AI_ANALYSIS_FILE, index=False)
                print("💾 Saved updated analysis with CoinGecko URLs")
                
                # Filter for tokens where at least one agent recommended BUY
                # and market cap is under MAX_MARKET_CAP
                buy_recommendations = full_analysis[
                    ((full_analysis['agent_one_recommendation'] == 'BUY') | 
                    (full_analysis['agent_two_recommendation'] == 'BUY')) &
                    (full_analysis['market_cap'] <= MAX_MARKET_CAP)
                ]
                
                # Sort by timestamp descending to show newest first
                buy_recommendations = buy_recommendations.sort_values('timestamp', ascending=False)
                
                # Save to new CSV
                buys_file = Path("src/data/ai_analysis_buys.csv")
                buy_recommendations.to_csv(buys_file, index=False)
                
                print(f"\n💰 Found {len(buy_recommendations)} buy recommendations under ${MAX_MARKET_CAP:,.0f} market cap")
                print(f"📝 Buy recommendations saved to: {buys_file.absolute()}")
                
            print("\n✨ Analysis round complete!")
            print(f"📊 Processed {len(discovered_tokens_df)} tokens")
            print(f"💾 Results saved to {AI_ANALYSIS_FILE}")
            
        except Exception as e:
            print(f"❌ Error in analysis cycle: {str(e)}")
            
        # Schedule next round
        next_run = datetime.now() + timedelta(hours=HOURS_BETWEEN_RUNS)
        print(f"\n⏳ Next round starts in {HOURS_BETWEEN_RUNS} hours (at {next_run.strftime('%H:%M:%S')})")



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