"""
🌙 Moon Dev's Strategy Agent
Handles all strategy-based trading decisions
"""

from src.config import *
import json
from termcolor import cprint
import openai
import os
import importlib
import inspect
import time
from src import nice_funcs as n
import pyttsx3
from transformers import pipeline

STRATEGY_EVAL_PROMPT = """
You are Moon Dev's Strategy Validation Assistant 🌙

Analyze the following strategy signals and validate their recommendations:

Strategy Signals:
{strategy_signals}

Market Context:
{market_data}

Your task:
1. Evaluate each strategy signal's reasoning
2. Check if signals align with current market conditions
3. Look for confirmation/contradiction between different strategies
4. Consider risk factors

Respond in this format:
1. First line: EXECUTE or REJECT for each signal (e.g., "EXECUTE signal_1, REJECT signal_2")
2. Then explain your reasoning:
   - Signal analysis
   - Market alignment
   - Risk assessment
   - Confidence in each decision (0-100%)

Remember:
- Moon Dev prioritizes risk management! 🛡️
- Multiple confirming signals increase confidence
- Contradicting signals require deeper analysis
- Better to reject a signal than risk a bad trade
"""

<<<<<<< HEAD
=======
AI_MODEL_OVERRIDE = "llama3.2"

>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007

class StrategyAgent:
    def __init__(self):
        self.enabled_strategies = []
<<<<<<< HEAD

        self.client = openai.OpenAI(
            base_url="http://localhost:11434/v1", api_key="ollama"
        )
=======
        self.client = openai.OpenAI(
            base_url="http://localhost:11434/v1", api_key="ollama"
        )
        self.model = AI_MODEL_OVERRIDE if AI_MODEL_OVERRIDE else AI_MODEL
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 150)
        self.engine.setProperty("volume", 0.9)
        self.sentiment = pipeline(
            "sentiment-analysis",
            model="finiteautomata/bertweet-base-sentiment-analysis",
        )

        if ENABLE_STRATEGIES:
            try:
<<<<<<< HEAD
                from src.strategies.custom.real_example_strategy import RealExampleStrategy

                self.enabled_strategies.extend([RealExampleStrategy()])
=======
                from src.strategies.custom.example_strategy import ExampleStrategy

                self.enabled_strategies.extend([ExampleStrategy()])
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
                print(f"✅ Loaded {len(self.enabled_strategies)} strategies!")
                for strategy in self.enabled_strategies:
                    print(f"  • {strategy.name}")
            except Exception as e:
                print(f"⚠️ Error loading strategies: {e}")
        else:
            print("🤖 Strategy Agent is disabled in config.py")

        print(
            f"🤖 Moon Dev's Strategy Agent initialized with {len(self.enabled_strategies)} strategies!"
        )

    def evaluate_signals(self, signals, market_data):
        try:
            if not signals:
                return None

            signals_str = json.dumps(signals, indent=2)

<<<<<<< HEAD
            message = self.client.chat.completions.create(
                model="deepseek-r1:1.5b",
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
=======
            response = self.client.chat.completions.create(
                model=self.model,  # Replace with your local model name
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
                messages=[
                    {
                        "role": "user",
                        "content": STRATEGY_EVAL_PROMPT.format(
                            strategy_signals=signals_str, market_data=market_data
                        ),
                    }
                ],
            )
<<<<<<< HEAD
            response = message.choices[0].message.content
=======
            response = response.choices[
                0
            ].message.content  # Extract the response content
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007

            lines = response.split("\n")
            decisions = lines[0].strip().split(",")
            reasoning = "\n".join(lines[1:])

            print("🤖 Strategy Evaluation:")
            print(f"Decisions: {decisions}")
            print(f"Reasoning: {reasoning}")

            return {"decisions": decisions, "reasoning": reasoning}

        except Exception as e:
            print(f"❌ Error evaluating signals: {e}")
            return None

    def get_signals(self, token):
        try:
            signals = []
            print(
                f"\n🔍 Analyzing {token} with {len(self.enabled_strategies)} strategies..."
            )

            for strategy in self.enabled_strategies:
                signal = strategy.generate_signals()
                if signal and signal["token"] == token:
                    signals.append(
                        {
                            "token": signal["token"],
                            "strategy_name": strategy.name,
                            "signal": signal["signal"],
                            "direction": signal["direction"],
                            "metadata": signal.get("metadata", {}),
                        }
                    )

            if not signals:
                print(f"ℹ️ No strategy signals for {token}")
                return []

            print(f"\n📊 Raw Strategy Signals for {token}:")
            for signal in signals:
                print(
                    f"  • {signal['strategy_name']}: {signal['direction']} ({signal['signal']}) for {signal['token']}"
                )

            try:
                from src.data.ohlcv_collector import collect_token_data

                market_data = collect_token_data(token)
            except Exception as e:
                print(f"⚠️ Could not get market data: {e}")
                market_data = {}

            print("\n🤖 Getting LLM evaluation of signals...")
            evaluation = self.evaluate_signals(signals, market_data)

            if not evaluation:
                print("❌ Failed to get LLM evaluation")
                return []

            approved_signals = []
            for signal, decision in zip(signals, evaluation["decisions"]):
                if "EXECUTE" in decision.upper():
                    print(
                        f"✅ LLM approved {signal['strategy_name']}'s {signal['direction']} signal"
                    )
                    approved_signals.append(signal)
                else:
                    print(
                        f"❌ LLM rejected {signal['strategy_name']}'s {signal['direction']} signal"
                    )

            if approved_signals:
                print(f"\n🎯 Final Approved Signals for {token}:")
                for signal in approved_signals:
                    print(
                        f"  • {signal['strategy_name']}: {signal['direction']} ({signal['signal']})"
                    )

                print("\n💫 Executing approved strategy signals...")
                self.execute_strategy_signals(approved_signals)
            else:
                print(f"\n⚠️ No signals approved by LLM for {token}")

            return approved_signals

        except Exception as e:
            print(f"❌ Error getting strategy signals: {e}")
            return []

    def combine_with_portfolio(self, signals, current_portfolio):
        try:
            final_allocations = current_portfolio.copy()

            for signal in signals:
                token = signal["token"]
                strength = signal["signal"]
                direction = signal["direction"]

                if direction == "BUY" and strength >= STRATEGY_MIN_CONFIDENCE:
                    print(f"🔵 Buy signal for {token} (strength: {strength})")
                    max_position = usd_size * (MAX_POSITION_PERCENTAGE / 100)
                    allocation = max_position * strength
                    final_allocations[token] = allocation
                elif direction == "SELL" and strength >= STRATEGY_MIN_CONFIDENCE:
                    print(f"🔴 Sell signal for {token} (strength: {strength})")
                    final_allocations[token] = 0

            return final_allocations

        except Exception as e:
            print(f"❌ Error combining signals: {e}")
            return None

    def execute_strategy_signals(self, approved_signals):
        try:
            if not approved_signals:
                print("⚠️ No approved signals to execute")
                return

            print("\n🚀 Moon Dev executing strategy signals...")
            print(f"📝 Received {len(approved_signals)} signals to execute")

            for signal in approved_signals:
                try:
                    print(f"\n🔍 Processing signal: {signal}")

                    token = signal.get("token")
                    if not token:
                        print("❌ Missing token in signal")
                        print(f"Signal data: {signal}")
                        continue

                    strength = signal.get("signal", 0)
                    direction = signal.get("direction", "NOTHING")

                    if token in EXCLUDED_TOKENS:
                        print(f"💵 Skipping {token} (excluded token)")
                        continue

                    print(f"\n🎯 Processing signal for {token}...")

                    max_position = usd_size * (MAX_POSITION_PERCENTAGE / 100)
                    target_size = max_position * strength

                    current_position = n.get_token_balance_usd(token)

                    print(f"📊 Signal strength: {strength}")
                    print(f"🎯 Target position: ${target_size:.2f} USD")
                    print(f"📈 Current position: ${current_position:.2f} USD")

<<<<<<< HEAD
                    sentiment_score = self.sentiment(token)[0]["score"]
                    target_size *= sentiment_score
                    self._announce(
                        f"Executing {direction} for {token} with strength {strength}"
                    )
=======
                    if self.use_local:
                        sentiment_score = self.sentiment(token)[0]["score"]
                        target_size *= sentiment_score
                        self._announce(
                            f"Executing {direction} for {token} with strength {strength}"
                        )
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007

                    if direction == "BUY":
                        if current_position < target_size:
                            print(f"✨ Executing BUY for {token}")
                            n.ai_entry(token, target_size)
                            print(f"✅ Entry complete for {token}")
                        else:
                            print(f"⏸️ Position already at or above target size")

                    elif direction == "SELL":
                        if current_position > 0:
                            print(f"📉 Executing SELL for {token}")
                            n.chunk_kill(token, max_usd_order_size, slippage)
                            print(f"✅ Exit complete for {token}")
                        else:
                            print(f"⏸️ No position to sell")

                    time.sleep(2)

                except Exception as e:
                    print(f"❌ Error processing signal: {str(e)}")
                    print(f"Signal data: {signal}")
                    continue

        except Exception as e:
            print(f"❌ Error executing strategy signals: {str(e)}")
            print("🔧 Moon Dev suggests checking the logs and trying again!")

    def _announce(self, message):
        print(f"\n🗣️ {message}")
<<<<<<< HEAD
        self.engine.say(message)
        self.engine.runAndWait()


if __name__ == "__main__":
    # Initialize the StrategyAgent
    agent = StrategyAgent()

    # Define a token to test (use one from your MONITORED_TOKENS list in config.py)
    test_token = "CR7ux8AY8a6pJD9ekLDPi19u2ujFNSvBFgUh36sBJU2W"  # Example token (FART)

    # Get signals for the test token
    print(f"\n🔍 Testing StrategyAgent with token: {test_token}")
    signals = agent.get_signals(test_token)

    # Print the results
    if signals:
        print("\n✅ Signals retrieved successfully:")
        for signal in signals:
            print(f"  • Strategy: {signal['strategy_name']}")
            print(f"    Direction: {signal['direction']}")
            print(f"    Signal Strength: {signal['signal']}")
            print(f"    Metadata: {signal['metadata']}")
    else:
        print("\n❌ No signals retrieved for the test token.")
=======
        if self.use_local:
            self.engine.say(message)
            self.engine.runAndWait()
<<<<<<< HEAD

#agent = StrategyAgent()
#signals = agent.get_signals("BTC")
=======
>>>>>>> c3be79076105d42d3e63e937514eb36d7155f542
>>>>>>> 08f5512040c5811ff908f0df6228e9b1d45cd007
