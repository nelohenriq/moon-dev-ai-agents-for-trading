Here’s the implementation of the VWAP-based trading strategy in Python using the `backtesting.py` framework. The code includes all the necessary components, such as indicators, entry/exit logic, risk management, and parameter optimization.

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np

# Data preprocessing
def preprocess_data(data_path):
    data = pd.read_csv(data_path)
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    # Ensure proper column mapping
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    # Convert datetime column
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data

# Strategy class
class VWAPStrategy(Strategy):
    # Parameters for optimization
    volume_threshold = 1.5  # Multiplier for average volume
    take_profit_pct = 0.01  # 1% take profit
    stop_loss_pct = 0.005   # 0.5% stop loss
    exit_time_window = 30   # 30-minute time-based exit

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        # Calculate average volume
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # Track entry time for time-based exits
        self.entry_time = None

    def next(self):
        # Check if we're in a trade
        if self.position:
            # Time-based exit
            if len(self.data) - self.entry_time >= self.exit_time_window:
                self.position.close()
                print(f"🌙 Time-based exit at {self.data.Close[-1]} ✨")
                return

            # Take profit or stop loss
            if self.position.is_long:
                if self.data.Close[-1] >= self.position.entry_price * (1 + self.take_profit_pct):
                    self.position.close()
                    print(f"🚀 Take profit hit at {self.data.Close[-1]} 🌙")
                elif self.data.Close[-1] <= self.position.entry_price * (1 - self.stop_loss_pct):
                    self.position.close()
                    print(f"🌑 Stop loss hit at {self.data.Close[-1]} ✨")
            elif self.position.is_short:
                if self.data.Close[-1] <= self.position.entry_price * (1 - self.take_profit_pct):
                    self.position.close()
                    print(f"🚀 Take profit hit at {self.data.Close[-1]} 🌙")
                elif self.data.Close[-1] >= self.position.entry_price * (1 + self.stop_loss_pct):
                    self.position.close()
                    print(f"🌑 Stop loss hit at {self.data.Close[-1]} ✨")
            return

        # Entry logic
        if self.data.Volume[-1] > self.avg_volume[-1] * self.volume_threshold:
            if crossover(self.data.Close, self.vwap):
                # Bullish entry
                self.buy()
                self.entry_time = len(self.data)
                print(f"🌙 Bullish entry at {self.data.Close[-1]} ✨")
            elif crossover(self.vwap, self.data.Close):
                # Bearish entry
                self.sell()
                self.entry_time = len(self.data)
                print(f"🌑 Bearish entry at {self.data.Close[-1]} ✨")

# Load and preprocess data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = preprocess_data(data_path)

# Run initial backtest
bt = Backtest(data, VWAPStrategy, cash=1_000_000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    volume_threshold=[1.2, 1.5, 2.0],
    take_profit_pct=[0.005, 0.01, 0.02],
    stop_loss_pct=[0.0025, 0.005, 0.01],
    exit_time_window=[15, 30, 60],
    maximize='Return [%]'
)
print(optimization_results)
bt.plot()
```

### Explanation of the Code:
1. **Data Preprocessing**:
   - Cleans column names and drops unnamed columns.
   - Ensures proper column mapping for `backtesting.py`.

2. **Strategy Class**:
   - Uses VWAP and average volume as indicators.
   - Implements entry logic based on price crossing VWAP with volume confirmation.
   - Includes take profit, stop loss, and time-based exit rules.

3. **Risk Management**:
   - Position sizing is handled by the `backtesting.py` framework.
   - Risk-reward ratio is controlled via `take_profit_pct` and `stop_loss_pct`.

4. **Parameter Optimization**:
   - Optimizes `volume_threshold`, `take_profit_pct`, `stop_loss_pct`, and `exit_time_window`.

5. **Moon Dev Themed Debug Prints**:
   - Adds emojis and themed messages for entry/exit signals.

6. **Backtest Execution**:
   - Runs an initial backtest with default parameters.
   - Prints full stats and plots the performance.
   - Runs optimization and displays the results.

### Notes:
- Replace the `data_path` with your actual data file path.
- Adjust the optimization ranges based on your specific requirements.
- Ensure you have the `backtesting.py` library installed (`pip install backtesting`).

Let me know if you need further assistance! 🌙✨🚀