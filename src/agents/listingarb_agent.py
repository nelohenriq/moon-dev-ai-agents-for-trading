import os
import pandas as pd
import json
from typing import Dict, List
from datetime import datetime, timedelta
import time
from pathlib import Path
from termcolor import colored, cprint
from openai import OpenAI  # Using OpenAI library for Ollama
from dotenv import load_dotenv
import requests
import numpy as np
import concurrent.futures

# Load environment variables
load_dotenv()

# ⚙️ Configuration
HOURS_BETWEEN_RUNS = 24        # Run AI analysis every 24 hours to manage API costs
PARALLEL_PROCESSES = 50        # Number of parallel processes to run
MIN_VOLUME_USD = 100_000      # Minimum 24h volume to analyze
MAX_MARKET_CAP = 10_000_000   # Maximum market cap to include in analysis (10M)

# 🤖 Tokens to Ignore
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

# 🤖 Agent Model Selection (Ollama models)
AGENT_ONE_MODEL = "deepseek-r1:1.5b"  # Technical Analysis Agent
AGENT_TWO_MODEL = "deepseek-r1:1.5b"  # Fundamental Analysis Agent

# 📁 File Paths
DISCOVERED_TOKENS_FILE = Path("src/data/discovered_tokens.csv")  # Input from token discovery script
AI_ANALYSIS_FILE = Path("src/data/ai_analysis.csv")  # AI analysis results

# 🤖 CoinGecko API Settings
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://pro-api.coingecko.com/api/v3"
TEMP_DATA_DIR = Path("src/data/temp_data")

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
        self.client = OpenAI(
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
        
    # ... (rest of the ListingArbSystem class remains unchanged)

def main():
    """Main function to run the Listing Arb system"""
    print("\n🌙 Moon Dev's Listing Arb System Starting Up! 🚀")
    print(f"⚙️ Configuration:")
    print(f"  • Hours between full runs: {HOURS_BETWEEN_RUNS}")
    print(f"  • Parallel processes: {PARALLEL_PROCESSES}")
    print(f"  • Minimum volume: ${MIN_VOLUME_USD:,.2f}")
    print(f"📝 Reading discovered tokens from: {DISCOVERED_TOKENS_FILE.absolute()}")
    print(f"📝 Saving AI analysis to: {AI_ANALYSIS_FILE.absolute()}")
    
    system = ListingArbSystem()
    
    try:
        round_number = 1
        while True:
            print(f"\n🔄 Starting Round {round_number}")
            system.run_analysis_cycle()
            
            next_round = datetime.now() + timedelta(hours=HOURS_BETWEEN_RUNS)
            print(f"\n⏳ Next round starts in {HOURS_BETWEEN_RUNS} hours (at {next_round.strftime('%H:%M:%S')})")
            time.sleep(HOURS_BETWEEN_RUNS * 3600)
            round_number += 1
            
    except KeyboardInterrupt:
        print("\n👋 Moon Dev's Listing Arb System signing off!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()