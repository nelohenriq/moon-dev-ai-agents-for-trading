Here’s the implementation of the **VWAP Volume Spike Strategy** in Python using the `backtesting.py` framework. The code includes all the necessary components, such as indicators, entry/exit logic, risk management, and parameter optimization. I’ve also added Moon Dev-themed debug prints for better visualization and debugging.

---

### Full Implementation

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder

# Clean and prepare the data
def prepare_data(data_path):
    data = pd.read_csv(data_path)
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    # Map columns to required format
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'datetime': 'Date'
    })
    # Convert Date column to datetime
    data['Date'] = pd.to_datetime(data['Date'])
    data.set_index('Date', inplace=True)
    return data

# Strategy Class
class VWAPVolumeSpike(Strategy):
    # Parameters
    volume_spike_threshold = 2.0  # Default volume spike threshold (2x average volume)
    avg_volume_period = 20  # Period for calculating average volume
    take_profit_pct = 0.01  # 1% take profit
    stop_loss_pct = 0.005  # 0.5% stop loss
    max_trade_duration = 30  # Max trade duration in minutes

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        # Calculate average volume
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=self.avg_volume_period)
        # Debug prints
        print("🌙 Moon Dev Strategy Initialized! 🚀")
        print(f"Volume Spike Threshold: {self.volume_spike_threshold}x")
        print(f"Average Volume Period: {self.avg_volume_period} periods")
        print(f"Take Profit: {self.take_profit_pct * 100}%")
        print(f"Stop Loss: {self.stop_loss_pct * 100}%")
        print(f"Max Trade Duration: {self.max_trade_duration} minutes")

    def next(self):
        # Skip if average volume is not calculated yet
        if len(self.avg_volume) < self.avg_volume_period:
            return

        # Calculate current volume spike condition
        current_volume = self.data.Volume[-1]
        avg_volume = self.avg_volume[-1]
        volume_spike = current_volume > (avg_volume * self.volume_spike_threshold)

        # Long Entry Condition
        if volume_spike and self.data.Close[-1] > self.vwap[-1] and not self.position:
            # Calculate position size based on risk management
            risk_amount = self.equity * 0.01  # Risk 1% of equity
            stop_loss_price = self.data.Close[-1] * (1 - self.stop_loss_pct)
            position_size = risk_amount / (self.data.Close[-1] - stop_loss_price)
            # Enter long position
            self.buy(size=position_size)
            print(f"🚀 Long Entry Signal! 🌙 Price: {self.data.Close[-1]}, Volume Spike: {current_volume / avg_volume:.2f}x")

        # Short Entry Condition
        elif volume_spike and self.data.Close[-1] < self.vwap[-1] and not self.position:
            # Calculate position size based on risk management
            risk_amount = self.equity * 0.01  # Risk 1% of equity
            stop_loss_price = self.data.Close[-1] * (1 + self.stop_loss_pct)
            position_size = risk_amount / (stop_loss_price - self.data.Close[-1])
            # Enter short position
            self.sell(size=position_size)
            print(f"🚀 Short Entry Signal! 🌙 Price: {self.data.Close[-1]}, Volume Spike: {current_volume / avg_volume:.2f}x")

        # Exit Conditions
        if self.position:
            # Take Profit or Stop Loss
            if self.position.is_long:
                take_profit_price = self.position.entry_price * (1 + self.take_profit_pct)
                stop_loss_price = self.position.entry_price * (1 - self.stop_loss_pct)
                if self.data.Close[-1] >= take_profit_price or self.data.Close[-1] <= stop_loss_price:
                    self.position.close()
                    print(f"🌙 Long Exit Signal! 🚀 Price: {self.data.Close[-1]}, PnL: {self.position.pl:.2f}")
            elif self.position.is_short:
                take_profit_price = self.position.entry_price * (1 - self.take_profit_pct)
                stop_loss_price = self.position.entry_price * (1 + self.stop_loss_pct)
                if self.data.Close[-1] <= take_profit_price or self.data.Close[-1] >= stop_loss_price:
                    self.position.close()
                    print(f"🌙 Short Exit Signal! 🚀 Price: {self.data.Close[-1]}, PnL: {self.position.pl:.2f}")

            # Time-Based Exit
            if len(self.data) - self.position.entry_bar >= self.max_trade_duration:
                self.position.close()
                print(f"🌙 Time-Based Exit! 🚀 Trade Duration Exceeded {self.max_trade_duration} minutes")

# Load and prepare data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = prepare_data(data_path)

# Initialize and run backtest
bt = Backtest(data, VWAPVolumeSpike, cash=1_000_000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)

# Plot initial results
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    volume_spike_threshold=[1.5, 2.0, 2.5, 3.0],
    avg_volume_period=[10, 20, 30],
    take_profit_pct=[0.005, 0.01, 0.02],
    stop_loss_pct=[0.005, 0.01, 0.015],
    max_trade_duration=[15, 30, 45],
    maximize='Return [%]'
)
print(optimization_results)

# Plot optimized results
bt.plot()
```

---

### Key Features:
1. **Indicators**:
   - VWAP and average volume are calculated using `talib`.
   - Volume spike condition is checked against the average volume.

2. **Entry/Exit Logic**:
   - Long entry when price is above VWAP and volume spike occurs.
   - Short entry when price is below VWAP and volume spike occurs.
   - Exit based on take profit, stop loss, or time-based conditions.

3. **Risk Management**:
   - Position sizing based on 1% risk per trade.
   - Stop loss and take profit levels are calculated dynamically.

4. **Parameter Optimization**:
   - Optimizes volume spike threshold, average volume period, take profit, stop loss, and trade duration.

5. **Moon Dev Debug Prints**:
   - Entry/exit signals are printed with Moon Dev-themed messages for easy debugging.

---

### Execution Order:
1. Run the initial backtest with default parameters.
2. Print full stats and strategy details.
3. Show the initial performance plot.
4. Run parameter optimization.
5. Show optimized results and final plot.

---

Let me know if you need further adjustments or additional features! 🌙✨🚀