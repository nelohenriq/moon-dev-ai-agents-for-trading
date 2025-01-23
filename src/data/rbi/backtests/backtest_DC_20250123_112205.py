Here’s the implementation of the **VWAP + Volume Spike** strategy in Python using the `backtesting.py` framework. The code includes all necessary components, such as indicators, entry/exit logic, risk management, and parameter optimization.

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder

# Clean and prepare the data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")
data.columns = data.columns.str.strip().str.lower()  # Clean column names
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])  # Drop unnamed columns
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)  # Map columns to required format
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class VWAPVolumeSpikeStrategy(Strategy):
    # Strategy parameters
    volume_spike_multiplier = 2.0  # Volume spike threshold (e.g., 2x average volume)
    risk_per_trade = 0.01  # Risk 1% of account per trade
    risk_reward_ratio = 2.0  # Risk-reward ratio for take profit
    atr_period = 14  # ATR period for dynamic stop loss

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)

        # Calculate average volume for the last 20 candles
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)

        # Calculate ATR for dynamic stop loss
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)

        # Debug prints
        print("🌙 Moon Dev Strategy Initialized! 🚀")
        print(f"Volume Spike Multiplier: {self.volume_spike_multiplier}")
        print(f"Risk per Trade: {self.risk_per_trade * 100}%")
        print(f"Risk-Reward Ratio: {self.risk_reward_ratio}")

    def next(self):
        # Check if we have enough data
        if len(self.data) < 20:
            return

        # Calculate volume spike condition
        volume_spike = self.data.Volume[-1] > self.volume_spike_multiplier * self.avg_volume[-1]

        # Long Entry Logic
        if (crossover(self.data.Close, self.vwap) and  # Price crosses above VWAP
            volume_spike and  # Volume spike occurs
            self.data.Close[-1] > self.data.Open[-1]):  # Bullish price action (close > open)
            
            # Calculate position size based on risk management
            stop_loss_price = self.data.Low[-1] - self.atr[-1]  # Stop loss below recent low minus ATR
            position_size = (self.equity * self.risk_per_trade) / (self.data.Close[-1] - stop_loss_price)
            
            # Place buy order
            self.buy(size=position_size, sl=stop_loss_price, tp=self.data.Close[-1] + self.risk_reward_ratio * (self.data.Close[-1] - stop_loss_price))
            print(f"🌙 Long Entry Signal! 🚀 | Price: {self.data.Close[-1]} | VWAP: {self.vwap[-1]} | Volume Spike: {self.data.Volume[-1]}")

        # Short Entry Logic
        elif (crossunder(self.data.Close, self.vwap) and  # Price crosses below VWAP
              volume_spike and  # Volume spike occurs
              self.data.Close[-1] < self.data.Open[-1]):  # Bearish price action (close < open)
            
            # Calculate position size based on risk management
            stop_loss_price = self.data.High[-1] + self.atr[-1]  # Stop loss above recent high plus ATR
            position_size = (self.equity * self.risk_per_trade) / (stop_loss_price - self.data.Close[-1])
            
            # Place sell order
            self.sell(size=position_size, sl=stop_loss_price, tp=self.data.Close[-1] - self.risk_reward_ratio * (stop_loss_price - self.data.Close[-1]))
            print(f"🌙 Short Entry Signal! 🚀 | Price: {self.data.Close[-1]} | VWAP: {self.vwap[-1]} | Volume Spike: {self.data.Volume[-1]}")

# Run initial backtest
bt = Backtest(data, VWAPVolumeSpikeStrategy, cash=1_000_000, commission=0.002)
stats = bt.run()
print(stats)
print(stats._strategy)

# Show initial performance plot
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    volume_spike_multiplier=range(1, 3, 0.5),  # Test volume spike thresholds
    risk_reward_ratio=range(1, 3, 0.5),  # Test risk-reward ratios
    maximize='Return [%]'
)
print(optimization_results)

# Show optimized results and final plot
bt.plot()
```

---

### Key Features of the Implementation:
1. **Indicators**:
   - VWAP is calculated using `talib.VWAP`.
   - Average volume is calculated using `talib.SMA`.
   - ATR is used for dynamic stop loss placement.

2. **Entry Logic**:
   - Long entries occur when:
     - Price crosses above VWAP.
     - A volume spike is detected.
     - Bullish price action (close > open) is confirmed.
   - Short entries occur when:
     - Price crosses below VWAP.
     - A volume spike is detected.
     - Bearish price action (close < open) is confirmed.

3. **Risk Management**:
   - Position sizing is based on a fixed risk percentage (1% of equity).
   - Stop loss is placed below the recent low (for long) or above the recent high (for short), adjusted by ATR.
   - Take profit is set based on a risk-reward ratio (e.g., 2:1).

4. **Parameter Optimization**:
   - The `volume_spike_multiplier` and `risk_reward_ratio` are optimized using ranges.

5. **Moon Dev Themed Debugging**:
   - Debug prints include emojis and clear messages for entry signals and strategy initialization.

---

### Execution Order:
1. Run the initial backtest with default parameters.
2. Print full statistics and strategy details.
3. Show the initial performance plot.
4. Optimize parameters for `volume_spike_multiplier` and `risk_reward_ratio`.
5. Show the optimized results and final plot.

---

Let me know if you need further adjustments or additional features! 🌙✨🚀