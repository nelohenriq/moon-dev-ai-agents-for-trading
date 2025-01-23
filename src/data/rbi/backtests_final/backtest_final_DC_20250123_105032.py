import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, resample_apply

# Clean and preprocess data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class MarketStructureStrategy(Strategy):
    # Strategy parameters
    fib_level_1 = 0.382  # Fibonacci retracement level 1
    fib_level_2 = 0.5    # Fibonacci retracement level 2 (50%)
    fib_level_3 = 0.618  # Fibonacci retracement level 3
    risk_per_trade = 0.01  # Risk 1% of account per trade
    risk_reward_ratio = 2  # Minimum risk-reward ratio
    swing_period = 20  # Period for identifying swing highs/lows

    def init(self):
        # Calculate swing highs and lows
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)

        # Calculate Fibonacci retracement levels
        self.fib_382 = self.I(self.calculate_fib, level=self.fib_level_1)
        self.fib_50 = self.I(self.calculate_fib, level=self.fib_level_2)
        self.fib_618 = self.I(self.calculate_fib, level=self.fib_level_3)

        # Debug prints
        print("🌙 Moon Dev Strategy Initialized! 🚀")
        print(f"Fibonacci Levels: {self.fib_level_1}, {self.fib_level_2}, {self.fib_level_3}")
        print(f"Risk per Trade: {self.risk_per_trade * 100}%")
        print(f"Risk-Reward Ratio: {self.risk_reward_ratio}")

    def calculate_fib(self, level):
        # Calculate Fibonacci retracement levels based on swing highs and lows
        return self.swing_low + (self.swing_high - self.swing_low) * level

    def next(self):
        # Skip if swing highs/lows are not yet calculated
        if len(self.data) < self.swing_period:
            return

        # Determine market structure (bullish or bearish)
        if self.swing_high[-1] > self.swing_high[-2] and self.swing_low[-1] > self.swing_low[-2]:
            market_structure = "bullish"
        elif self.swing_high[-1] < self.swing_high[-2] and self.swing_low[-1] < self.swing_low[-2]:
            market_structure = "bearish"
        else:
            market_structure = "neutral"

        # Define premium and discount zones
        discount_zone = self.data.Close[-1] < self.fib_50[-1]
        premium_zone = self.data.Close[-1] > self.fib_50[-1]

        # Identify confluence areas (order blocks or fair value gaps)
        confluence_area = self.identify_confluence()

        # Multi-timeframe confirmation (simplified for backtesting)
        if market_structure == "bullish" and discount_zone and confluence_area:
            self.enter_bullish_trade()
        elif market_structure == "bearish" and premium_zone and confluence_area:
            self.enter_bearish_trade()

    def identify_confluence(self):
        # Simplified confluence identification (order block or fair value gap)
        # For backtesting, we assume confluence exists if price is near a Fibonacci level
        if abs(self.data.Close[-1] - self.fib_382[-1]) < 10 or abs(self.data.Close[-1] - self.fib_618[-1]) < 10:
            return True
        return False

    def enter_bullish_trade(self):
        # Calculate position size based on risk management
        risk_amount = self.equity * self.risk_per_trade
        stop_loss = self.swing_low[-1]  # Stop loss below the swing low
        take_profit = self.swing_high[-1]  # Take profit at the next swing high
        risk_reward = (take_profit - self.data.Close[-1]) / (self.data.Close[-1] - stop_loss)

        if risk_reward >= self.risk_reward_ratio:
            # Enter the trade
            self.buy(size=risk_amount / (self.data.Close[-1] - stop_loss), sl=stop_loss, tp=take_profit)
            print(f"🌙 Bullish Trade Entered! 🚀 | Entry: {self.data.Close[-1]}, SL: {stop_loss}, TP: {take_profit}")

    def enter_bearish_trade(self):
        # Calculate position size based on risk management
        risk_amount = self.equity * self.risk_per_trade
        stop_loss = self.swing_high[-1]  # Stop loss above the swing high
        take_profit = self.swing_low[-1]  # Take profit at the next swing low
        risk_reward = (self.data.Close[-1] - take_profit) / (stop_loss - self.data.Close[-1])

        if risk_reward >= self.risk_reward_ratio:
            # Enter the trade
            self.sell(size=risk_amount / (stop_loss - self.data.Close[-1]), sl=stop_loss, tp=take_profit)
            print(f"🌙 Bearish Trade Entered! 🚀 | Entry: {self.data.Close[-1]}, SL: {stop_loss}, TP: {take_profit}")

# Run the backtest
bt = Backtest(data, MarketStructureStrategy, cash=1_000_000, commission=0.002)
stats = bt.run()
print(stats)
print(stats._strategy)

# Plot the results
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    fib_level_1=range(30, 40, 2),
    fib_level_2=range(45, 55, 2),
    fib_level_3=range(60, 70, 2),
    risk_reward_ratio=range(2, 6),
    maximize='Return [%]'
)
print(optimization_results)

# Plot optimized results
bt.plot()