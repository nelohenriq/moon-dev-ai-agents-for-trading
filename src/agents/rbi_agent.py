"""
🌙 Moon Dev's RBI Agent (Research-Backtest-Implement)
Built with love by Moon Dev 🚀

Required Setup:
1. Create folder structure:
   src/
   ├── data/
   │   └── rbi/
   │       ├── research/         # Strategy research outputs
   │       ├── backtests/        # Initial backtest code
   │       ├── backtests_final/  # Debugged backtest code
   │       ├── BTC-USD-15m.csv  # Price data for backtesting
   │       └── ideas.txt        # Trading ideas to process

2. Environment Variables:
   - DEEPSEEK_KEY: Your DeepSeek API key

3. Create ideas.txt:
   - One trading idea per line
   - Can be YouTube URLs, PDF links, or text descriptions
   - Lines starting with # are ignored

This agent automates the RBI process:
1. Research: Analyzes trading strategies from various sources
2. Backtest: Creates backtests for promising strategies
3. Debug: Fixes technical issues in generated backtests

Remember: Past performance doesn't guarantee future results!
"""

# DeepSeek Model Selection per Agent
# Set to "0" to use config.py's AI_MODEL setting
# Options for each: "deepseek-chat" (faster) or "deepseek-reasoner" (more analytical)
RESEARCH_MODEL ="deepseek-r1-distill-llama-70b"  # use ollama locally "deepseek-r1:1.5b" # use groq model deepseek-r1-distill-llama-70b # Analyzes strategies thoroughly
BACKTEST_MODEL ="deepseek-r1-distill-llama-70b"  # use ollama locally "deepseek-r1:1.5b" # use groq model deepseek-r1-distill-llama-70b # Creative in implementing strategies
DEBUG_MODEL ="deepseek-r1-distill-llama-70b"  # use ollama locally "qwen2.5-coder:3b"    # use groq model deepseek-r1-distill-llama-70b # Careful code analysis

# Agent Prompts

RESEARCH_PROMPT = """
You are Moon Dev's Research AI 🌙

IMPORTANT NAMING RULES:
1. Create a UNIQUE TWO-WORD NAME for this specific strategy
2. The name must be DIFFERENT from any generic names like "TrendFollower" or "MomentumStrategy"
3. First word should describe the main approach (e.g., Adaptive, Neural, Quantum, Fractal, Dynamic)
4. Second word should describe the specific technique (e.g., Reversal, Breakout, Oscillator, Divergence)
5. Make the name SPECIFIC to this strategy's unique aspects

Examples of good names:
- "AdaptiveBreakout" for a strategy that adjusts breakout levels
- "FractalMomentum" for a strategy using fractal analysis with momentum
- "QuantumReversal" for a complex mean reversion strategy
- "NeuralDivergence" for a strategy focusing on divergence patterns

BAD names to avoid:
- "TrendFollower" (too generic)
- "SimpleMoving" (too basic)
- "PriceAction" (too vague)

Output format must start with:
STRATEGY_NAME: [Your unique two-word name]

Then analyze the trading strategy content and create detailed instructions.
Focus on:
1. Key strategy components
2. Entry/exit rules
3. Risk management
4. Required indicators

STRATEGY_DETAILS:
[Your detailed analysis]

Remember: The name must be UNIQUE and SPECIFIC to this strategy's approach!
"""

BACKTEST_PROMPT = """
You are Moon Dev's Backtest AI 🌙
Create a backtesting.py implementation for the strategy.
Include:
1. All necessary imports
2. Strategy class with indicators
3. Entry/exit logic
4. Risk management
5. Parameter optimization
6. your size should be 1,000,000
7. If you need indicators use TA lib or pandas TA. Do not use backtesting.py's indicators. 

IMPORTANT DATA HANDLING:
1. Clean column names by removing spaces: data.columns = data.columns.str.strip().str.lower()
2. Drop any unnamed columns: data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
3. Ensure proper column mapping to match backtesting requirements:
   - Required columns: 'Open', 'High', 'Low', 'Close', 'Volume'
   - Use proper case (capital first letter)
4. When optimizing parameters:
   - Never try to optimize lists directly
   - Break down list parameters (like Fibonacci levels) into individual parameters
   - Use ranges for optimization (e.g., fib_level_1=range(30, 40, 2))

INDICATOR CALCULATION RULES:
1. ALWAYS use self.I() wrapper for ANY indicator calculations
2. Use talib functions instead of pandas operations:
   - Instead of: self.data.Close.rolling(20).mean()
   - Use: self.I(talib.SMA, self.data.Close, timeperiod=20)
3. For swing high/lows use talib.MAX/MIN:
   - Instead of: self.data.High.rolling(window=20).max()
   - Use: self.I(talib.MAX, self.data.High, timeperiod=20)

BACKTEST EXECUTION ORDER:
1. Run initial backtest with default parameters first
2. Print full stats using print(stats) and print(stats._strategy)
3. Show initial performance plot
4. Then run optimization
5. Show optimized results and final plot

CHART OUTPUT:
1. Import os at the top of the file
2. Save charts to the charts directory:
   ```python
   # Save plots to charts directory
   chart_file = os.path.join("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts", f"{strategy_name}_chart.html")
   bt.plot(filename=chart_file, open_browser=False)
   ```
3. Do this for both initial and optimized plots

RISK MANAGEMENT:
1. Always calculate position sizes based on risk percentage
2. Use proper stop loss and take profit calculations
3. Include risk-reward ratio in optimization parameters
4. Print entry/exit signals with Moon Dev themed messages

If you need indicators use TA lib or pandas TA. Do not use backtesting.py's indicators. 

Use this data path: /Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv
the above data head looks like below
datetime, open, high, low, close, volume,
2023-01-01 00:00:00, 16531.83, 16532.69, 16509.11, 16510.82, 231.05338022,
2023-01-01 00:15:00, 16509.78, 16534.66, 16509.11, 16533.43, 308.12276951,

Always add plenty of Moon Dev themed debug prints with emojis to make debugging easier! 🌙 ✨ 🚀
"""

DEBUG_PROMPT = """
You are Moon Dev's Debug AI 🌙
Fix technical issues in the backtest code WITHOUT changing the strategy logic.
Focus on:
1. Syntax errors (like incorrect string formatting)
2. Import statements and dependencies
3. Class and function definitions
4. Variable scoping and naming
5. Print statement formatting

DO NOT change:
1. Strategy logic
2. Entry/exit conditions
3. Risk management rules
4. Parameter values

Return the complete fixed code.
"""

PACKAGE_PROMPT = """
You are Moon Dev's Package AI 🌙
Your job is to ensure the backtest code NEVER uses ANY backtesting.lib imports or functions.

❌ STRICTLY FORBIDDEN:
1. from backtesting.lib import *
2. import backtesting.lib
3. from backtesting.lib import crossover
4. ANY use of backtesting.lib

✅ REQUIRED REPLACEMENTS:
1. For crossover detection:
   Instead of: backtesting.lib.crossover(a, b)
   Use: (a[-2] < b[-2] and a[-1] > b[-1])  # for bullish crossover
        (a[-2] > b[-2] and a[-1] < b[-1])  # for bearish crossover

2. For indicators:
   - Use talib for all standard indicators (SMA, RSI, MACD, etc.)
   - Use pandas-ta for specialized indicators
   - ALWAYS wrap in self.I()

3. For signal generation:
   - Use numpy/pandas boolean conditions
   - Use rolling window comparisons with array indexing
   - Use mathematical comparisons (>, <, ==)

Example conversions:
❌ from backtesting.lib import crossover
❌ if crossover(fast_ma, slow_ma):
✅ if fast_ma[-2] < slow_ma[-2] and fast_ma[-1] > slow_ma[-1]:

❌ self.sma = self.I(backtesting.lib.SMA, self.data.Close, 20)
✅ self.sma = self.I(talib.SMA, self.data.Close, timeperiod=20)

IMPORTANT: Scan the ENTIRE code for any backtesting.lib usage and replace ALL instances!
Return the complete fixed code with proper Moon Dev themed debug prints! 🌙 ✨
"""

def get_model_id(model):
    """Get DR/DC identifier based on model type"""
    if "7b" in model:
        return "DR"  # Deep Reasoner for 7B models
    elif "1.5b" in model:
        return "DC"  # Deep Coder for 1.5B models
    elif "coder" in model.lower():
        return "CD"  # Deep Coder for coder models
    else:
        return "DR"  # Default to DR for other cases

import os
import time
import re
from datetime import datetime
import requests
from io import BytesIO
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from pathlib import Path
from termcolor import cprint
import threading
import itertools
import sys
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

os.environ['LANGSMITH_TRACING'] = 'true'
os.environ['LANGSMITH_ENDPOINT'] = "https://api.smith.langchain.com"
os.environ['LANGSMITH_API_KEY'] = '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'
os.environ['LANGSMITH_PROJECT'] = 'pr-charming-personnel-66'

# DeepSeek Configuration
DEEPSEEK_BASE_URL = "http://localhost:11434/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Update data directory paths
PROJECT_ROOT = Path(__file__).parent.parent  # Points to src/
DATA_DIR = PROJECT_ROOT / "data/rbi"
RESEARCH_DIR = DATA_DIR / "research"
BACKTEST_DIR = DATA_DIR / "backtests"
PACKAGE_DIR = DATA_DIR / "backtests_package"
FINAL_BACKTEST_DIR = DATA_DIR / "backtests_final"
CHARTS_DIR = DATA_DIR / "charts"  # New directory for HTML charts

print(f"📂 Using RBI data directory: {DATA_DIR}")
print(f"📂 Research directory: {RESEARCH_DIR}")
print(f"📂 Backtest directory: {BACKTEST_DIR}")
print(f"📂 Package directory: {PACKAGE_DIR}")
print(f"📂 Final backtest directory: {FINAL_BACKTEST_DIR}")
print(f"📈 Charts directory: {CHARTS_DIR}")

@traceable
def init_deepseek_client():
    """Initialize DeepSeek client with proper error handling"""
    try:
        #deepseek_key = os.getenv("DEEPSEEK_KEY")
        # if not deepseek_key:
        #    raise ValueError("🚨 DEEPSEEK_KEY not found in environment variables!")
            
        print("🔑 Initializing DeepSeek client...")
        print("🌟 Moon Dev's RBI Agent is connecting to DeepSeek...")
        
        """ client = openai.OpenAI(
            base_url=DEEPSEEK_BASE_URL,
            api_key="ollama"
        ) """

        groq_api_key = os.getenv('OPENAI_KEY')

        client = openai.OpenAI(
            base_url=GROQ_BASE_URL,
            api_key=groq_api_key
        )
        
        print("✅ DeepSeek client initialized successfully!")
        print("🚀 Moon Dev's RBI Agent ready to roll!")
        return client
    except Exception as e:
        print(f"❌ Error initializing DeepSeek client: {str(e)}")
        print("💡 Check if your DEEPSEEK_KEY is valid and properly set")
        return None

@traceable
def chat_with_deepseek(system_prompt, user_content, model):
    """Chat with DeepSeek API using specified model"""
    print(f"\n🤖 Starting chat with DeepSeek using {model}...")
    print("🌟 Moon Dev's RBI Agent is thinking...")
    
    client = init_deepseek_client()
    if not client:
        print("❌ Failed to initialize DeepSeek client")
        return None
        
    try:
        print("📤 Sending request to DeepSeek API...")
        print(f"🎯 Model: {model}")
        print("🔄 Please wait while Moon Dev's RBI Agent processes your request...")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.0
        )
        
        if not response or not response.choices:
            print("❌ Empty response from DeepSeek API")
            return None
            
        print("📥 Received response from DeepSeek API!")
        print(f"✨ Response length: {len(response.choices[0].message.content)} characters")
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error in DeepSeek chat: {str(e)}")
        print("💡 This could be due to API rate limits or invalid requests")
        print(f"🔍 Error details: {str(e)}")
        return None

@traceable
def get_youtube_transcript(video_id):
    """Get transcript from YouTube video"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_generated_transcript(['en'])
        cprint("📺 Successfully fetched YouTube transcript!", "green")
        return ' '.join([t['text'] for t in transcript.fetch()])
    except Exception as e:
        cprint(f"❌ Error fetching transcript: {e}", "red")
        return None

@traceable
def get_pdf_text(url):
    """Extract text from PDF URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        reader = PyPDF2.PdfReader(BytesIO(response.content))
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        cprint("📚 Successfully extracted PDF text!", "green")
        return text
    except Exception as e:
        cprint(f"❌ Error reading PDF: {e}", "red")
        return None

def animate_progress(agent_name, stop_event):
    """Fun animation while agent is thinking"""
    spinners = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
    messages = [
        "brewing coffee ☕️",
        "studying charts 📊",
        "checking signals 📡",
        "doing math 🔢",
        "reading docs 📚",
        "analyzing data 🔍",
        "making magic ✨",
        "trading secrets 🤫",
        "Moon Dev approved 🌙",
        "to the moon! 🚀"
    ]
    
    spinner = itertools.cycle(spinners)
    message = itertools.cycle(messages)
    
    while not stop_event.is_set():
        sys.stdout.write('\033[K')  # Clear the current line
        sys.stdout.write(f'\r{next(spinner)} {agent_name} is {next(message)}...')
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write('\033[K')  # Clear the line when done
    sys.stdout.write('\r')
    sys.stdout.flush()

def run_with_animation(func, agent_name, *args, **kwargs):
    """Run a function with a fun loading animation"""
    stop_animation = threading.Event()
    animation_thread = threading.Thread(target=animate_progress, args=(agent_name, stop_animation))
    
    try:
        animation_thread.start()
        result = func(*args, **kwargs)
        return result
    finally:
        stop_animation.set()
        animation_thread.join()

@traceable
def research_strategy(content):
    """Research Agent: Analyzes and creates trading strategy"""
    cprint("\n🔍 Starting Research Agent...\n", "cyan")
    cprint("🤖 Time to discover some alpha!", "yellow")
    
    output = run_with_animation(
        chat_with_deepseek,
        "Research Agent",
        RESEARCH_PROMPT, 
        content, 
        RESEARCH_MODEL
    )
    
    if output:
        strategy_name = "UnknownStrategy"  # Default name
        if "STRATEGY_NAME:" in output:
            strategy_name = output.split("STRATEGY_NAME:")[1].split("\n")[0].strip()
            # Clean up strategy name to be file-system friendly
            strategy_name = re.sub(r'[^\w\s-]', '', strategy_name)
            strategy_name = re.sub(r'[\s]+', '', strategy_name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Save research output
        filepath = RESEARCH_DIR / f"{strategy_name}_strategy.txt"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"📝 Research Agent found something spicy! Saved to {filepath} 🌶️", "green")
        cprint(f"🏷️ Generated strategy name: {strategy_name}", "yellow")
        return output, strategy_name
    return None, None

@traceable
def create_backtest(strategy, strategy_name="UnknownStrategy"):
    """Backtest Agent: Creates backtest implementation"""
    cprint("\n📊 Starting Backtest Agent...\n", "cyan")
    cprint("💰 Let's turn that strategy into profits!", "yellow")
    
    output = run_with_animation(
        chat_with_deepseek,
        "Backtest Agent",
        BACKTEST_PROMPT,
        f"Create a backtest for this strategy:\n\n{strategy}",
        BACKTEST_MODEL
    )
    
    if output:
        filepath = BACKTEST_DIR / f"{strategy_name}_BT.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"🔥 Backtest Agent cooked up some heat! Saved to {filepath} 🚀", "green")
        return output
    return None

@traceable
def debug_backtest(backtest_code, strategy=None, strategy_name="UnknownStrategy"):
    """Debug Agent: Fixes technical issues in backtest code"""
    cprint("\n🔧 Starting Debug Agent...\n", "cyan")
    cprint("🔍 Time to squash some bugs!", "yellow")
    
    context = f"Here's the backtest code to debug:\n\n{backtest_code}"
    if strategy:
        context += f"\n\nOriginal strategy for reference:\n{strategy}"
    
    output = run_with_animation(
        chat_with_deepseek,
        "Debug Agent",
        DEBUG_PROMPT,
        context,
        DEBUG_MODEL
    )
    
    if output:
        code_match = re.search(r'```python\n(.*?)\n```', output, re.DOTALL)
        if code_match:
            output = code_match.group(1)
            
        # Save to final directory with strategy name
        filepath = FINAL_BACKTEST_DIR / f"{strategy_name}_BTFinal.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"🔧 Debug Agent fixed the code! Saved to {filepath} ✨", "green")
        return output
    return None

@traceable
def package_check(backtest_code, strategy_name="UnknownStrategy"):
    """Package Agent: Ensures correct indicator packages are used"""
    cprint("\n📦 Starting Package Agent...\n", "cyan")
    cprint("🔍 Checking for proper indicator imports!", "yellow")
    
    output = run_with_animation(
        chat_with_deepseek,
        "Package Agent",
        PACKAGE_PROMPT,
        f"Check and fix indicator packages in this code:\n\n{backtest_code}",
        DEBUG_MODEL
    )
    
    if output:
        code_match = re.search(r'```python\n(.*?)\n```', output, re.DOTALL)
        if code_match:
            output = code_match.group(1)
            
        # Save to package directory
        filepath = PACKAGE_DIR / f"{strategy_name}_PKG.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"📦 Package Agent optimized the imports! Saved to {filepath} ✨", "green")
        return output
    return None

@traceable
def get_idea_content(idea_url: str) -> str:
    """Extract content from a trading idea URL or text"""
    print("\n📥 Extracting content from idea...")
    
    try:
        if "youtube.com" in idea_url or "youtu.be" in idea_url:
            # Extract video ID from URL
            if "v=" in idea_url:
                video_id = idea_url.split("v=")[1].split("&")[0]
            else:
                video_id = idea_url.split("/")[-1].split("?")[0]
            
            print("🎥 Detected YouTube video, fetching transcript...")
            transcript = get_youtube_transcript(video_id)
            if transcript:
                print("✅ Successfully extracted YouTube transcript!")
                return f"YouTube Strategy Content:\n\n{transcript}"
            else:
                raise ValueError("Failed to extract YouTube transcript")
                
        elif idea_url.endswith(".pdf"):
            print("📚 Detected PDF file, extracting text...")
            pdf_text = get_pdf_text(idea_url)
            if pdf_text:
                print("✅ Successfully extracted PDF content!")
                return f"PDF Strategy Content:\n\n{pdf_text}"
            else:
                raise ValueError("Failed to extract PDF text")
                
        else:
            print("📝 Using raw text input...")
            return f"Text Strategy Content:\n\n{idea_url}"
            
    except Exception as e:
        print(f"❌ Error extracting content: {str(e)}")
        raise

@traceable
def process_trading_idea(link: str) -> None:
    """Process a trading idea by detecting type and extracting content"""
    print("\n🚀 Moon Dev's RBI Agent Processing New Idea!")
    print("🌟 Let's find some alpha in the chaos!")

    
    try:
        # Create output directories if they don't exist
        for dir in [DATA_DIR, RESEARCH_DIR, BACKTEST_DIR, FINAL_BACKTEST_DIR]:
            dir.mkdir(parents=True, exist_ok=True)
            
        print("💭 Processing raw strategy idea...")

        ## Step 1: Extract content from the idea
        idea_content = get_idea_content(link)
        if not idea_content:
            print("❌ Failed to extract content from idea!")
            return
            
        print(f"📄 Extracted content length: {len(idea_content)} characters")
        
        # Phase 1: Research
        print("\n🧪 Phase 1: Research")
        strategy, strategy_name = research_strategy(idea_content)
        
        if not strategy:
            print("❌ Research phase failed!")
            return
        
        print(f"🏷️ Strategy Name: {strategy_name}")

        # Save strategy to file with timestamp
        strategy_file = RESEARCH_DIR / f"strategy_DC_{strategy_name}.txt"
        with open(strategy_file, "w") as f:
            f.write(strategy)
        print(f"\n📝 Strategy saved to {strategy_file}")
        
        # Phase 2: Backtest
        print("\n📈 Phase 2: Backtest")
        backtest = create_backtest(strategy, strategy_name)
        
        if not backtest:
            print("❌ Backtest phase failed!")
            return

        # Save initial backtest
        backtest_file = BACKTEST_DIR / f"backtest_DC_{strategy_name}.py"
        with open(backtest_file, "w") as f:
            f.write(backtest)

        # Phase 3: Package Check using only the backtest code
        print("\n📦 Phase 3: Package Check")
        package_checked = package_check(backtest, strategy_name)
        
        if not package_checked:
            print("❌ Package check failed!")
            return
            
        # Save package check output
        package_file = PACKAGE_DIR / f"{strategy_name}_PKG.py"
        with open(package_file, 'w') as f:
            f.write(package_checked)
            
        # Phase 4: Debug using only the package-checked code
        print("\n🔧 Phase 4: Debug")
        final_backtest = debug_backtest(package_checked, strategy, strategy_name)
        
        if not final_backtest:
            print("❌ Debug phase failed!")
            return
            
        # Save final backtest
        final_file = FINAL_BACKTEST_DIR / f"{strategy_name}.py"
        with open(final_file, 'w') as f:
            f.write(final_backtest)
            
        print("\n🎉 Mission Accomplished!")
        print(f"🚀 Strategy '{strategy_name}' is ready to make it rain! 💸")
        print(f"✨ Final backtest saved at: {final_file}")
        
    except Exception as e:
        print(f"\n❌ Error processing idea: {str(e)}")
        raise

@traceable
def debug_existing_backtests():
    """Debug all existing backtests in the backtests directory"""
    cprint("\n🔍 Looking for existing backtests to debug...", "cyan")
    
    backtest_files = list(BACKTEST_DIR.glob("*.py"))
    if not backtest_files:
        cprint("❌ No backtest files found!", "yellow")
        return
        
    for backtest_file in backtest_files:
        cprint(f"\n🔧 Debugging {backtest_file.name}...", "cyan")
        
        # Read the backtest code
        with open(backtest_file, 'r') as f:
            backtest_code = f.read()
            
        # Try to find corresponding strategy file
        strategy_timestamp = backtest_file.stem.replace('backtest_', '')
        strategy_file = RESEARCH_DIR / f"strategy_{strategy_timestamp}.txt"
        strategy = None
        if strategy_file.exists():
            with open(strategy_file, 'r') as f:
                strategy = f.read()
                
        # Debug the backtest
        debugged_code = debug_backtest(backtest_code, strategy)
        if debugged_code:
            output_file = FINAL_BACKTEST_DIR / f"backtest_final_{get_model_id(DEBUG_MODEL)}_{backtest_file.name}"
            with open(output_file, 'w') as f:
                f.write(debugged_code)
            cprint(f"✨ Saved debugged version to {output_file}", "green")
        else:
            cprint(f"❌ Failed to debug {backtest_file.name}", "red")

@traceable
def main():
    """Main function to process ideas from file"""
    ideas_file = DATA_DIR / "ideas.txt"
    
    if not ideas_file.exists():
        cprint("❌ ideas.txt not found! Creating template...", "red")
        ideas_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ideas_file, 'w') as f:
            f.write("# Add your trading ideas here (one per line)\n")
            f.write("# Can be YouTube URLs, PDF links, or text descriptions\n")
        return
        
    with open(ideas_file, 'r') as f:
        ideas = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    total_ideas = len(ideas)
    cprint(f"\n🎯 Found {total_ideas} trading ideas to process", "cyan")

    for i, idea in enumerate(ideas, 1):
        cprint(f"\n{'='*100}", "yellow")
        cprint(f"🌙 Processing idea {i}/{total_ideas}", "cyan")
        cprint(f"📝 Idea content: {idea[:100]}{'...' if len(idea) > 100 else ''}", "yellow")
        cprint(f"{'='*100}\n", "yellow")
        
        try:
            # Process each idea in complete isolation
            process_trading_idea(idea)
            
            # Clear separator between ideas
            cprint(f"\n{'='*100}", "green")
            cprint(f"✅ Completed idea {i}/{total_ideas}", "green")
            cprint(f"{'='*100}\n", "green")
            
            # Break between ideas
            if i < total_ideas:
                cprint("😴 Taking a break before next idea...", "yellow")
                time.sleep(5)
                
        except Exception as e:
            cprint(f"\n❌ Error processing idea {i}: {str(e)}", "red")
            cprint("🔄 Continuing with next idea...\n", "yellow")
            continue

if __name__ == "__main__":
    try:
        cprint(f"\n🌟 Moon Dev's RBI Agent Starting Up!", "green")
        cprint(f"🤖 Using Research Model: {RESEARCH_MODEL}", "cyan")
        cprint(f"📊 Using Backtest Model: {BACKTEST_MODEL}", "cyan")
        cprint(f"🔧 Using Debug Model: {DEBUG_MODEL}", "cyan")
        main()
    except KeyboardInterrupt:
        cprint("\n👋 Moon Dev's RBI Agent shutting down gracefully...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
