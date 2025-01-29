"""
🌊 Moon Dev's Liquidation Monitor
Built with love by Moon Dev 🚀

Luna the Liquidation Agent tracks sudden increases in liquidation volume and announces when she sees potential market moves

Need an API key? for a limited time, bootcamp members get free api keys for claude, openai, helius, birdeye & quant elite gets access to the moon dev api. join here: https://algotradecamp.com
"""

import os
import pandas as pd
import time
from datetime import datetime, timedelta, timezone
from termcolor import colored, cprint
from dotenv import load_dotenv
from openai import OpenAI  # Use OpenAI client for Ollama
from pathlib import Path
from src import nice_funcs as n
from src import nice_funcs_hl as hl
from src.agents.api import MoonDevAPI
from collections import deque
from src.agents.base_agent import BaseAgent
import traceback
import numpy as np
import pyttsx3  # Add pyttsx3 for TTS

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
CHECK_INTERVAL_MINUTES = 10  # How often to check liquidations
LIQUIDATION_ROWS = 10000  # Number of rows to fetch each time
LIQUIDATION_THRESHOLD = (
    0.5  # Multiplier for average liquidation to detect significant events
)

# OHLCV Data Settings
TIMEFRAME = "15m"  # Candlestick timeframe
LOOKBACK_BARS = 100  # Number of candles to analyze

# Select which time window to use for comparisons (options: 15, 60, 240)
# 15 = 15 minutes (most reactive to sudden changes)
# 60 = 1 hour (medium-term changes)
# 240 = 4 hours (longer-term changes)
COMPARISON_WINDOW = 15  # Default to 15 minutes for quick reactions

# AI Settings - Override config.py if set
from src import config

# Only set these if you want to override config.py settings
AI_MODEL = "llama3.2"  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE
AI_MAX_TOKENS = 100  # Set > 0 to override config.AI_MAX_TOKENS

# Voice settings (pyttsx3)
VOICE_NAME = "nova"  # Not used in pyttsx3, but kept for compatibility
VOICE_SPEED = 1  # Not used in pyttsx3, but kept for compatibility

# AI Analysis Prompt
LIQUIDATION_ANALYSIS_PROMPT = """
You are a precise trading assistant. Your response must follow this EXACT format:

LINE 1: Type ONLY one of these words: BUY, SELL, or NOTHING
LINE 2: Brief reason (10 words or less)
LINE 3: Type "Confidence: " followed by a number 0-100 and "%"

Market Data:
- Total Liquidation Change: {pct_change}%
- Long Liquidations: ${current_longs:,.2f} ({pct_change_longs:+.1f}%)
- Short Liquidations: ${current_shorts:,.2f} ({pct_change_shorts:+.1f}%)

Technical Context:
{market_data}
<<<<<<< HEAD
=======

Large long liquidations often indicate potential bottoms (shorts taking profit)
Large short liquidations often indicate potential tops (longs taking profit)
Consider the ratio of long vs short liquidations and their relative changes
**IMPORTANT**: Respond ONLY in the required 3-line format. Do not include any additional text or explanations.
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
"""


class LiquidationAgent(BaseAgent):
    """Luna the Liquidation Monitor 🌊"""

    def __init__(self):
        """Initialize Luna the Liquidation Agent"""
        super().__init__("liquidation")

        # Set AI parameters - use config values unless overridden
        self.ai_model = AI_MODEL if AI_MODEL else config.AI_MODEL
        self.ai_temperature = (
            AI_TEMPERATURE if AI_TEMPERATURE > 0 else config.AI_TEMPERATURE
        )
        self.ai_max_tokens = (
            AI_MAX_TOKENS if AI_MAX_TOKENS > 0 else config.AI_MAX_TOKENS
        )

        print(f"🤖 Using AI Model: {self.ai_model}")
        if AI_MODEL or AI_TEMPERATURE > 0 or AI_MAX_TOKENS > 0:
            print("⚠️ Note: Using some override settings instead of config.py defaults")
            if AI_MODEL:
                print(f"  - Model: {AI_MODEL}")
            if AI_TEMPERATURE > 0:
                print(f"  - Temperature: {AI_TEMPERATURE}")
            if AI_MAX_TOKENS > 0:
                print(f"  - Max Tokens: {AI_MAX_TOKENS}")

        load_dotenv()

        # Initialize Ollama client
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",  # Ollama's OpenAI-compatible endpoint
            api_key="ollama",  # API key is not required for Ollama
        )

        self.api = MoonDevAPI()

        # Create data directories if they don't exist
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.data_dir = PROJECT_ROOT / "src" / "data"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize or load historical data
        self.history_file = self.data_dir / "liquidation_history.csv"
        self.load_history()

        # Initialize pyttsx3 TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty("rate", 150)  # Speed of speech
        self.tts_engine.setProperty("volume", 1.0)  # Volume level (0.0 to 1.0)

        print("🌊 Luna the Liquidation Agent initialized!")
<<<<<<< HEAD
        print(
            f"🎯 Alerting on liquidation increases above {(LIQUIDATION_THRESHOLD-1)*100:.0f}%"
        )
=======
        print(f"🎯 Alerting on liquidation increases above +{LIQUIDATION_THRESHOLD*100:.0f}% from previous")
>>>>>>> c3be79076105d42d3e63e937514eb36d7155f542
        print(f"📊 Analyzing last {LIQUIDATION_ROWS} liquidation events")
        print(f"📈 Using {LOOKBACK_BARS} {TIMEFRAME} candles for market context")

    def load_history(self):
        """Load or initialize historical liquidation data"""
        try:
            if self.history_file.exists():
                self.liquidation_history = pd.read_csv(self.history_file)

                # Handle transition from old format to new format
                if "long_size" not in self.liquidation_history.columns:
                    print(
                        "📝 Converting history to new format with long/short tracking..."
                    )
                    # Assume 50/50 split for old records (we'll get accurate data on next update)
                    self.liquidation_history["long_size"] = (
                        self.liquidation_history["total_size"] / 2
                    )
                    self.liquidation_history["short_size"] = (
                        self.liquidation_history["total_size"] / 2
                    )

                print(
                    f"📈 Loaded {len(self.liquidation_history)} historical liquidation records"
                )
            else:
                self.liquidation_history = pd.DataFrame(
                    columns=["timestamp", "long_size", "short_size", "total_size"]
                )
                print("📝 Created new liquidation history file")

            # Clean up old data (keep only last 24 hours)
            if not self.liquidation_history.empty:
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.liquidation_history = self.liquidation_history[
                    pd.to_datetime(self.liquidation_history["timestamp"]) > cutoff_time
                ]
                self.liquidation_history.to_csv(self.history_file, index=False)

        except Exception as e:
            print(f"❌ Error loading history: {str(e)}")
            self.liquidation_history = pd.DataFrame(
                columns=["timestamp", "long_size", "short_size", "total_size"]
            )

    def _get_current_liquidations(self):
        """Get current liquidation data"""
        try:
            print("\n🔍 Fetching fresh liquidation data...")
            df = self.api.get_liquidation_data(limit=LIQUIDATION_ROWS)

            if df is not None and not df.empty:
                # Set column names
                df.columns = [
                    "symbol",
                    "side",
                    "type",
                    "time_in_force",
                    "quantity",
                    "price",
                    "price2",
                    "status",
                    "filled_qty",
                    "total_qty",
                    "timestamp",
                    "usd_value",
                ]

                # Convert timestamp to datetime (UTC)
<<<<<<< HEAD
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
                current_time = datetime.utcnow()

=======
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
<<<<<<< HEAD
                current_time = datetime.utcnow()
=======
                current_time = datetime.datetime.now(datetime.UTC)
                
>>>>>>> c3be79076105d42d3e63e937514eb36d7155f542
                # Calculate time windows
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
                fifteen_min = current_time - timedelta(minutes=15)
                one_hour = current_time - timedelta(hours=1)
                four_hours = current_time - timedelta(hours=4)

                # Separate long and short liquidations
                longs = df[df["side"] == "SELL"]  # SELL side = long liquidation
                shorts = df[df["side"] == "BUY"]  # BUY side = short liquidation

                # Calculate totals for each time window and type
                fifteen_min_longs = longs[longs["datetime"] >= fifteen_min][
                    "usd_value"
                ].sum()
                fifteen_min_shorts = shorts[shorts["datetime"] >= fifteen_min][
                    "usd_value"
                ].sum()
                one_hour_longs = longs[longs["datetime"] >= one_hour]["usd_value"].sum()
                one_hour_shorts = shorts[shorts["datetime"] >= one_hour][
                    "usd_value"
                ].sum()
                four_hour_longs = longs[longs["datetime"] >= four_hours][
                    "usd_value"
                ].sum()
                four_hour_shorts = shorts[shorts["datetime"] >= four_hours][
                    "usd_value"
                ].sum()

                # Get event counts
                fifteen_min_long_events = len(longs[longs["datetime"] >= fifteen_min])
                fifteen_min_short_events = len(
                    shorts[shorts["datetime"] >= fifteen_min]
                )
                one_hour_long_events = len(longs[longs["datetime"] >= one_hour])
                one_hour_short_events = len(shorts[shorts["datetime"] >= one_hour])
                four_hour_long_events = len(longs[longs["datetime"] >= four_hours])
                four_hour_short_events = len(shorts[shorts["datetime"] >= four_hours])

                # Calculate percentage change for active window
                pct_change_longs = 0
                pct_change_shorts = 0
                if not self.liquidation_history.empty:
                    previous_record = self.liquidation_history.iloc[-1]
                    if COMPARISON_WINDOW == 60:
                        current_longs = one_hour_longs
                        current_shorts = one_hour_shorts
                    elif COMPARISON_WINDOW == 240:
                        current_longs = four_hour_longs
                        current_shorts = four_hour_shorts
                    else:
                        current_longs = fifteen_min_longs
                        current_shorts = fifteen_min_shorts

                    if (
                        "long_size" in previous_record
                        and previous_record["long_size"] > 0
                    ):
                        pct_change_longs = (
                            (current_longs - previous_record["long_size"])
                            / previous_record["long_size"]
                        ) * 100
                    if (
                        "short_size" in previous_record
                        and previous_record["short_size"] > 0
                    ):
                        pct_change_shorts = (
                            (current_shorts - previous_record["short_size"])
                            / previous_record["short_size"]
                        ) * 100

                # Print fun box with liquidation info
                print("\n" + "╔" + "═" * 70 + "╗")
                print(
                    "║                🌙 Moon Dev's Liquidation Party 💦                 ║"
                )
                print("╠" + "═" * 70 + "╣")

                # Format each line based on which window is active
                if COMPARISON_WINDOW == 15:
                    print(
                        f"║  Last 15min LONGS:  ${fifteen_min_longs:,.2f} ({fifteen_min_long_events} events) [{pct_change_longs:+.1f}%]".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 15min SHORTS: ${fifteen_min_shorts:,.2f} ({fifteen_min_short_events} events) [{pct_change_shorts:+.1f}%]".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 1hr LONGS:    ${one_hour_longs:,.2f} ({one_hour_long_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 1hr SHORTS:   ${one_hour_shorts:,.2f} ({one_hour_short_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 4hrs LONGS:   ${four_hour_longs:,.2f} ({four_hour_long_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 4hrs SHORTS:  ${four_hour_shorts:,.2f} ({four_hour_short_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                elif COMPARISON_WINDOW == 60:
                    print(
                        f"║  Last 15min LONGS:  ${fifteen_min_longs:,.2f} ({fifteen_min_long_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 15min SHORTS: ${fifteen_min_shorts:,.2f} ({fifteen_min_short_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 1hr LONGS:    ${one_hour_longs:,.2f} ({one_hour_long_events} events) [{pct_change_longs:+.1f}%]".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 1hr SHORTS:   ${one_hour_shorts:,.2f} ({one_hour_short_events} events) [{pct_change_shorts:+.1f}%]".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 4hrs LONGS:   ${four_hour_longs:,.2f} ({four_hour_long_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 4hrs SHORTS:  ${four_hour_shorts:,.2f} ({four_hour_short_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                else:  # 240 minutes (4 hours)
                    print(
                        f"║  Last 15min LONGS:  ${fifteen_min_longs:,.2f} ({fifteen_min_long_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 15min SHORTS: ${fifteen_min_shorts:,.2f} ({fifteen_min_short_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 1hr LONGS:    ${one_hour_longs:,.2f} ({one_hour_long_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 1hr SHORTS:   ${one_hour_shorts:,.2f} ({one_hour_short_events} events)".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 4hrs LONGS:   ${four_hour_longs:,.2f} ({four_hour_long_events} events) [{pct_change_longs:+.1f}%]".ljust(
                            71
                        )
                        + "║"
                    )
                    print(
                        f"║  Last 4hrs SHORTS:  ${four_hour_shorts:,.2f} ({four_hour_short_events} events) [{pct_change_shorts:+.1f}%]".ljust(
                            71
                        )
                        + "║"
                    )

                print("╚" + "═" * 70 + "╝")

                # Return the totals based on selected comparison window
                if COMPARISON_WINDOW == 60:
                    return one_hour_longs, one_hour_shorts
                elif COMPARISON_WINDOW == 240:
                    return four_hour_longs, four_hour_shorts
                else:  # Default to 15 minutes
                    return fifteen_min_longs, fifteen_min_shorts
            return None, None

        except Exception as e:
            print(f"❌ Error getting liquidation data: {str(e)}")
            traceback.print_exc()
            return None, None

    def _analyze_opportunity(
        self, current_longs, current_shorts, previous_longs, previous_shorts
    ):
        """Get AI analysis of the liquidation event"""
        try:
            # Calculate percentage changes
<<<<<<< HEAD
            pct_change_longs = ((current_longs - previous_longs) / previous_longs) * 100 if previous_longs > 0 else 0
            pct_change_shorts = ((current_shorts - previous_shorts) / previous_shorts) * 100 if previous_shorts > 0 else 0
            total_pct_change = ((current_longs + current_shorts - previous_longs - previous_shorts) / 
                            (previous_longs + previous_shorts)) * 100 if (previous_longs + previous_shorts) > 0 else 0
            
            # Get market data silently (XRP as per the example)
            market_data = hl.get_data(
                symbol="LINK",
=======
            pct_change_longs = (
                ((current_longs - previous_longs) / previous_longs) * 100
                if previous_longs > 0
                else 0
            )
            pct_change_shorts = (
                ((current_shorts - previous_shorts) / previous_shorts) * 100
                if previous_shorts > 0
                else 0
            )
            total_pct_change = (
                (
                    (current_longs + current_shorts - previous_longs - previous_shorts)
                    / (previous_longs + previous_shorts)
                )
                * 100
                if (previous_longs + previous_shorts) > 0
                else 0
            )

            # Get market data silently (BTC by default since it leads the market)
            market_data = hl.get_data(
                symbol="XRP",
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
                timeframe=TIMEFRAME,
                bars=LOOKBACK_BARS,
                add_indicators=True,
            )

            if market_data is None or market_data.empty:
                print(
                    "⚠️ Could not fetch market data, proceeding with liquidation analysis only"
                )
                market_data_str = "No market data available"
            else:
                # Format market data nicely - show last 5 candles
                market_data_str = market_data.tail(5).to_string()

            # Prepare the context
            context = LIQUIDATION_ANALYSIS_PROMPT.format(
                pct_change=f"{total_pct_change:.2f}",
                current_size=current_longs + current_shorts,
                previous_size=previous_longs + previous_shorts,
                LIQUIDATION_ROWS=LIQUIDATION_ROWS,
                current_longs=current_longs,
                current_shorts=current_shorts,
                pct_change_longs=pct_change_longs,
                pct_change_shorts=pct_change_shorts,
                LOOKBACK_BARS=LOOKBACK_BARS,
                TIMEFRAME=TIMEFRAME,
                market_data=market_data_str,
            )

            print(f"\n🤖 Analyzing liquidation spike with AI...")

<<<<<<< HEAD

            # Get AI analysis
            response = self.client.chat.completions.create(
                model=self.ai_model,
                messages=[{"role": "user", "content": context}],
=======
            # Get AI analysis using Ollama client
            response = self.client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": context},
                ],
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
                temperature=self.ai_temperature,
                max_tokens=self.ai_max_tokens,
            )
<<<<<<< HEAD
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response
            lines = ai_response.split('\n')
            if len(lines) >= 3:
                action = lines[0].strip().upper()
                reason = lines[1].strip()
                confidence = lines[2].split(':')[1].strip().rstrip('%')
                
                # Validate action
                if action not in ['BUY', 'SELL', 'NOTHING']:
                    action = 'NOTHING'
                    reason = 'Invalid AI response'
                    confidence = '0'
                
                # Ensure confidence is a valid number
                try:
                    confidence = int(confidence)
                except ValueError:
                    confidence = 0
                
                return action, reason, confidence
            else:
                return 'NOTHING', 'Invalid AI response format', 0
            
        except Exception as e:
            print(f"❌ Error in AI analysis: {str(e)}")
            traceback.print_exc()
            return 'NOTHING', 'Error in analysis', 0
            
=======

            # Handle response
            if not response or not response.choices:
                print("❌ No response from AI")
                return None

            # Extract the response text
            analysis = response.choices[0].message.content

            # Parse response - handle both newline and period-based splits
            lines = [line.strip() for line in analysis.split("\n") if line.strip()]
            if not lines:
                print("❌ Empty response from AI")
                return None

            # First line should be the action
            action = lines[0].strip().upper()
            if action not in ["BUY", "SELL", "NOTHING"]:
                print(f"⚠️ Invalid action: {action}. Defaulting to NOTHING.")
                action = "NOTHING"

            # Rest is analysis
            analysis = lines[1] if len(lines) > 1 else ""

            # Extract confidence from third line
            confidence = 50  # Default confidence
            if len(lines) > 2:
                try:
                    import re

                    matches = re.findall(r"(\d+)%", lines[2])
                    if matches:
                        confidence = int(matches[0])
                except:
                    print("⚠️ Could not parse confidence, using default")

            return {
                "action": action,
                "analysis": analysis,
                "confidence": confidence,
                "pct_change": total_pct_change,
                "pct_change_longs": pct_change_longs,
                "pct_change_shorts": pct_change_shorts,
            }

        except Exception as e:
            print(f"❌ Error in AI analysis: {str(e)}")
            traceback.print_exc()
            return None

>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
    def _format_announcement(self, analysis):
        """Format liquidation analysis into a speech-friendly message"""
        try:
            if analysis:
                # Determine which liquidation type was more significant
                if abs(analysis["pct_change_longs"]) > abs(
                    analysis["pct_change_shorts"]
                ):
                    liq_type = "LONG"
                    pct_change = analysis["pct_change_longs"]
                else:
                    liq_type = "SHORT"
<<<<<<< HEAD
                    pct_change = analysis["pct_change_shorts"]

=======
                    pct_change = analysis['pct_change_shorts']
                
                # Format the percentage change message
                if pct_change > 0:
                    change_msg = f"up {abs(pct_change):.1f}%"
                else:
                    change_msg = f"down {abs(pct_change):.1f}%"
                
>>>>>>> c3be79076105d42d3e63e937514eb36d7155f542
                message = (
                    f"ayo moon dev seven seven seven! "
                    f"Massive {liq_type} liquidations detected! "
                    f"{change_msg} in the last period! "
                    f"AI suggests {analysis['action']} with {analysis['confidence']}% confidence 🌙"
                )
                return message
            return None

        except Exception as e:
            print(f"❌ Error formatting announcement: {str(e)}")
            return None

    def _announce(self, message):
        if not message:
            return
        try:
            print(f"\n📢 Announcing: {message}")
            self.tts_engine.say(message)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"❌ Error in announcement: {str(e)}")

    def _save_to_history(self, long_size, short_size):
        """Save current liquidation data to history"""
        try:
            if long_size is not None and short_size is not None:
                # Create new row
                new_row = pd.DataFrame(
                    [
                        {
                            "timestamp": datetime.now(),
                            "long_size": long_size,
                            "short_size": short_size,
                            "total_size": long_size + short_size,
                        }
                    ]
                )

                # Add to history
                if self.liquidation_history.empty:
                    self.liquidation_history = new_row
                else:
                    self.liquidation_history = pd.concat(
                        [self.liquidation_history, new_row], ignore_index=True
                    )

                # Keep only last 24 hours
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.liquidation_history = self.liquidation_history[
                    pd.to_datetime(self.liquidation_history["timestamp"]) > cutoff_time
                ]

                # Save to file
                self.liquidation_history.to_csv(self.history_file, index=False)

        except Exception as e:
            print(f"❌ Error saving to history: {str(e)}")
            traceback.print_exc()

    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            # Get current liquidation data
            current_longs, current_shorts = self._get_current_liquidations()

            if current_longs is not None and current_shorts is not None:
                # Get previous size
                if not self.liquidation_history.empty:
                    previous_record = self.liquidation_history.iloc[-1]

                    # Handle missing columns gracefully
                    previous_longs = previous_record.get("long_size", 0)
                    previous_shorts = previous_record.get("short_size", 0)

                    # Only trigger if we have valid previous data
                    if previous_longs > 0 and previous_shorts > 0:
                        # Check if we have a significant increase in either longs or shorts
<<<<<<< HEAD
                        if current_longs > (
                            previous_longs * LIQUIDATION_THRESHOLD
                        ) or current_shorts > (previous_shorts * LIQUIDATION_THRESHOLD):
=======
                        # Adding 1 to threshold so 0.5 means 150% of previous value
                        threshold = 1 + LIQUIDATION_THRESHOLD
                        if (current_longs > (previous_longs * threshold) or 
                            current_shorts > (previous_shorts * threshold)):
>>>>>>> c3be79076105d42d3e63e937514eb36d7155f542
                            # Get AI analysis
                            analysis = self._analyze_opportunity(
                                current_longs,
                                current_shorts,
                                previous_longs,
                                previous_shorts,
                            )

                            if analysis:
                                # Format and announce
                                message = self._format_announcement(analysis)
                                if message:
                                    self._announce(message)

                                    # Print detailed analysis
                                    print("\n" + "╔" + "═" * 50 + "╗")
<<<<<<< HEAD
                                    print("║        🌙 Moon Dev's Liquidation Analysis 💦        ║")
=======
                                    print(
                                        "║        🌙 Moon Dev's Liquidation Analysis 💦       ║"
                                    )
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
                                    print("╠" + "═" * 50 + "╣")
                                    print(f"║  Action: {analysis['action']:<41} ║")
                                    print(
                                        f"║  Confidence: {analysis['confidence']}%{' '*36} ║"
                                    )
                                    analysis_lines = analysis["analysis"].split("\n")
                                    for line in analysis_lines:
                                        print(f"║  {line:<47} ║")
                                    print("╚" + "═" * 50 + "╝")

                # Save to history
                self._save_to_history(current_longs, current_shorts)

        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")
            traceback.print_exc()

    def run(self):
        """Run the liquidation monitor continuously"""
        print("\n🌊 Starting liquidation monitoring...")

        while True:
            try:
                self.run_monitoring_cycle()
                print(f"\n💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)

            except KeyboardInterrupt:
                print("\n👋 Luna the Liquidation Agent shutting down gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying


if __name__ == "__main__":
    agent = LiquidationAgent()
    agent.run()
