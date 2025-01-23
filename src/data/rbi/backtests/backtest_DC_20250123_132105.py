Here’s the implementation of the VWAP-based trading strategy in Python using the `backtesting.py` framework. The code includes all the necessary components, such as indicator calculations, entry/exit logic, risk management, and parameter optimization.

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np

# Clean and prepare the data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# Strategy Implementation
class VWAPStrategy(Strategy):
    # Parameters for optimization
    risk_per_trade = 0.01  # Risk 1% of equity per trade
    take_profit_pct = 0.01  # 1% take profit
    stop_loss_pct = 0.005  # 0.5% stop loss
    rsi_period = 14  # RSI period for momentum filter
    atr_period = 14  # ATR period for trailing stop

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        
        # Calculate RSI for momentum filter
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        
        # Calculate ATR for trailing stop
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        # Calculate average volume for confirmation
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        # Debug prints
        print("🌙 Moon Dev Strategy Initialized! 🚀")
        print(f"Risk per trade: {self.risk_per_trade * 100}%")
        print(f"Take profit: {self.take_profit_pct * 100}%")
        print(f"Stop loss: {self.stop_loss_pct * 100}%")

    def next(self):
        # Skip if VWAP or other indicators are not calculated yet
        if len(self.data.Close) < max(self.rsi_period, self.atr_period):
            return

        # Calculate position size based on risk management
        position_size = self.equity * self.risk_per_trade / (self.data.Close[-1] * self.stop_loss_pct)
        position_size = int(position_size)

        # Bullish Entry: Price crosses above VWAP, volume above average, and RSI > 50
        if (crossover(self.data.Close, self.vwap) and
            self.data.Volume[-1] > self.avg_volume[-1] and
            self.rsi[-1] > 50):
            self.buy(size=position_size)
            print(f"🌙 Bullish Entry! 🚀 Price: {self.data.Close[-1]}, VWAP: {self.vwap[-1]}, RSI: {self.rsi[-1]}")

        # Bearish Entry: Price crosses below VWAP, volume above average, and RSI < 50
        elif (crossover(self.vwap, self.data.Close) and
              self.data.Volume[-1] > self.avg_volume[-1] and
              self.rsi[-1] < 50):
            self.sell(size=position_size)
            print(f"🌙 Bearish Entry! 🚀 Price: {self.data.Close[-1]}, VWAP: {self.vwap[-1]}, RSI: {self.rsi[-1]}")

        # Take Profit and Stop Loss Logic
        for trade in self.trades:
            if trade.is_long:
                # Take profit for long positions
                if self.data.Close[-1] >= trade.entry_price * (1 + self.take_profit_pct):
                    self.position.close()
                    print(f"🌙 Take Profit Hit! 🚀 Long trade closed at {self.data.Close[-1]}")
                # Stop loss for long positions
                elif self.data.Close[-1] <= trade.entry_price * (1 - self.stop_loss_pct):
                    self.position.close()
                    print(f"🌙 Stop Loss Hit! 🚀 Long trade closed at {self.data.Close[-1]}")
            elif trade.is_short:
                # Take profit for short positions
                if self.data.Close[-1] <= trade.entry_price * (1 - self.take_profit_pct):
                    self.position.close()
                    print(f"🌙 Take Profit Hit! 🚀 Short trade closed at {self.data.Close[-1]}")
                # Stop loss for short positions
                elif self.data.Close[-1] >= trade.entry_price * (1 + self.stop_loss_pct):
                    self.position.close()
                    print(f"🌙 Stop Loss Hit! 🚀 Short trade closed at {self.data.Close[-1]}")

# Backtest Execution
bt = Backtest(data, VWAPStrategy, cash=1_000_000, commission=0.001)

# Initial backtest with default parameters
stats = bt.run()
print(stats)
print(stats._strategy)
bt.plot()

# Parameter Optimization
optimization_results = bt.optimize(
    risk_per_trade=[0.01, 0.02],  # Test 1% and 2% risk per trade
    take_profit_pct=[0.01, 0.02],  # Test 1% and 2% take profit
    stop_loss_pct=[0.005, 0.01],  # Test 0.5% and 1% stop loss
    rsi_period=range(10, 20, 2),  # Test RSI periods between 10 and 20
    atr_period=range(10, 20, 2),  # Test ATR periods between 10 and 20
    maximize='Sharpe Ratio'  # Optimize for Sharpe Ratio
)

print("🌙 Optimization Results 🚀")
print(optimization_results)

# Run backtest with optimized parameters
optimized_stats = bt.run(**optimization_results._strategy)
print(optimized_stats)
bt.plot()
```

### Key Features:
1. **Indicators**:
   - VWAP, RSI, ATR, and average volume are calculated using `talib`.
   - All indicators are wrapped in `self.I()` for compatibility with `backtesting.py`.

2. **Entry/Exit Logic**:
   - Bullish entry when price crosses above VWAP, volume is above average, and RSI > 50.
   - Bearish entry when price crosses below VWAP, volume is above average, and RSI < 50.
   - Take profit and stop loss are based on fixed percentages.

3. **Risk Management**:
   - Position size is calculated based on 1-2% risk per trade.
   - Stop loss and take profit levels are optimized.

4. **Optimization**:
   - Parameters like risk per trade, take profit, stop loss, RSI period, and ATR period are optimized.
   - Optimization maximizes the Sharpe Ratio.

5. **Moon Dev Themed Debug Prints**:
   - Debug prints include emojis for easy identification of signals and events.

6. **Data Handling**:
   - Data is cleaned and prepared to match the required format for `backtesting.py`.

### Execution Order:
1. Run the initial backtest with default parameters.
2. Print full stats and plot the initial performance.
3. Optimize parameters and print the results.
4. Run the backtest with optimized parameters and plot the final performance.

Let me know if you need further adjustments! 🌙✨🚀