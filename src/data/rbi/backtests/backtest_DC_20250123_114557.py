Here’s the implementation of the VWAP Trading Strategy in Python using the `backtesting.py` framework. The code includes all the necessary components, such as imports, strategy class, entry/exit logic, risk management, and parameter optimization.

```python
# Import necessary libraries
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Clean and prepare the data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")

# Clean column names
data.columns = data.columns.str.strip().str.lower()

# Drop any unnamed columns
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Convert datetime column to proper format
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

# Define the VWAP Trading Strategy
class VWAPStrategy(Strategy):
    # Strategy parameters
    risk_per_trade = 0.01  # Risk 1% of capital per trade
    risk_reward_ratio = 2  # Risk-reward ratio
    atr_period = 14  # ATR period for stop loss
    rsi_period = 14  # RSI period for confirmation
    vwap_lookback = 20  # Lookback period for VWAP

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume, timeperiod=self.vwap_lookback)
        
        # Calculate ATR for stop loss
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        # Calculate RSI for confirmation
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        
        # Debug prints
        print("🌙 Moon Dev VWAP Strategy Initialized! 🚀")
        print(f"Risk per trade: {self.risk_per_trade * 100}%")
        print(f"Risk-reward ratio: {self.risk_reward_ratio}")

    def next(self):
        # Skip if VWAP or ATR is not calculated yet
        if len(self.vwap) < self.vwap_lookback or len(self.atr) < self.atr_period:
            return

        # Calculate position size based on risk management
        stop_loss_distance = self.atr[-1]  # Use ATR for stop loss
        position_size = (self.equity * self.risk_per_trade) / stop_loss_distance
        position_size = int(position_size)

        # Mean-reversion entry logic
        if crossover(self.data.Close, self.vwap) and self.rsi[-1] < 70:  # Long entry
            self.buy(size=position_size, sl=self.data.Close[-1] - stop_loss_distance, tp=self.data.Close[-1] + (stop_loss_distance * self.risk_reward_ratio))
            print(f"🌙 Moon Dev Long Entry Signal! 🚀 Price: {self.data.Close[-1]}, VWAP: {self.vwap[-1]}, RSI: {self.rsi[-1]}")

        elif crossover(self.vwap, self.data.Close) and self.rsi[-1] > 30:  # Short entry
            self.sell(size=position_size, sl=self.data.Close[-1] + stop_loss_distance, tp=self.data.Close[-1] - (stop_loss_distance * self.risk_reward_ratio))
            print(f"🌙 Moon Dev Short Entry Signal! 🚀 Price: {self.data.Close[-1]}, VWAP: {self.vwap[-1]}, RSI: {self.rsi[-1]}")

        # Trend-following entry logic
        if self.data.Close[-1] > self.vwap[-1] and all(self.data.Close[-i] > self.vwap[-i] for i in range(1, 4)):  # Bullish trend
            self.buy(size=position_size, sl=self.data.Close[-1] - stop_loss_distance, tp=self.data.Close[-1] + (stop_loss_distance * self.risk_reward_ratio))
            print(f"🌙 Moon Dev Bullish Trend Entry! 🚀 Price: {self.data.Close[-1]}, VWAP: {self.vwap[-1]}")

        elif self.data.Close[-1] < self.vwap[-1] and all(self.data.Close[-i] < self.vwap[-i] for i in range(1, 4)):  # Bearish trend
            self.sell(size=position_size, sl=self.data.Close[-1] + stop_loss_distance, tp=self.data.Close[-1] - (stop_loss_distance * self.risk_reward_ratio))
            print(f"🌙 Moon Dev Bearish Trend Entry! 🚀 Price: {self.data.Close[-1]}, VWAP: {self.vwap[-1]}")

# Initialize backtest
bt = Backtest(data, VWAPStrategy, cash=1_000_000, commission=0.002)

# Run initial backtest
stats = bt.run()
print(stats)
print(stats._strategy)

# Show initial performance plot
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    risk_per_trade=[0.01, 0.02],
    risk_reward_ratio=[2, 3],
    atr_period=range(10, 20, 2),
    rsi_period=range(10, 20, 2),
    vwap_lookback=range(15, 25, 5),
    maximize='Return [%]'
)

# Print optimized results
print("🌙 Moon Dev Optimization Results! 🚀")
print(optimization_results)

# Show final performance plot with optimized parameters
bt.plot()
```

---

### Key Features:
1. **Indicators**:
   - VWAP, ATR, and RSI are calculated using `talib`.
   - Indicators are wrapped in `self.I()` for proper integration with `backtesting.py`.

2. **Entry/Exit Logic**:
   - Mean-reversion and trend-following entries are implemented.
   - Stop loss and take profit are calculated dynamically using ATR.

3. **Risk Management**:
   - Position size is calculated based on risk percentage and stop loss distance.
   - Risk-reward ratio is included in the optimization parameters.

4. **Optimization**:
   - Parameters like `risk_per_trade`, `risk_reward_ratio`, `atr_period`, `rsi_period`, and `vwap_lookback` are optimized.

5. **Moon Dev Themed Debug Prints**:
   - Debug prints include emojis and clear messages for easy tracking of signals.

---

### Execution Order:
1. Run the initial backtest with default parameters.
2. Print full stats and strategy details.
3. Show the initial performance plot.
4. Run optimization and print the results.
5. Show the final performance plot with optimized parameters.

---

Let me know if you need further adjustments or additional features! 🌙✨🚀