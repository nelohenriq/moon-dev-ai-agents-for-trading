Here’s the implementation of the VWAP-Based Trading Strategy in Python using the `backtesting.py` framework. The code includes all the necessary components, such as indicator calculations, entry/exit logic, risk management, and parameter optimization.

```python
# Import necessary libraries
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder

# Clean and preprocess data
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
    # Convert datetime column to datetime object
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data

# Define the VWAP-Based Trading Strategy
class VWAPStrategy(Strategy):
    # Strategy parameters
    vwap_period = 20  # VWAP calculation period
    trend_confirmation_candles = 3  # Number of candles for trend confirmation
    risk_per_trade = 0.01  # Risk per trade (1% of account equity)
    take_profit_pct = 0.01  # Take profit percentage (1%)
    stop_loss_pct = 0.005  # Stop loss percentage (0.5%)
    atr_period = 14  # ATR period for dynamic stop loss

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume, timeperiod=self.vwap_period)
        # Calculate ATR for dynamic stop loss
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        # Track consecutive candles above/below VWAP
        self.consecutive_above = 0
        self.consecutive_below = 0

    def next(self):
        # Calculate position size based on risk percentage
        position_size = self.equity * self.risk_per_trade / self.data.Close[-1]

        # Mean-Reversion Setup
        if crossover(self.data.Close, self.vwap):
            if self.position.is_short:
                self.position.close()
                print(f"🌙 Moon Dev Alert: Closing Short Position (Mean-Reversion) at {self.data.Close[-1]}")
            if not self.position.is_long:
                self.buy(size=position_size)
                print(f"🌙 Moon Dev Alert: Long Entry (Mean-Reversion) at {self.data.Close[-1]}")
                # Set take profit and stop loss
                take_profit = self.data.Close[-1] * (1 + self.take_profit_pct)
                stop_loss = self.data.Close[-1] * (1 - self.stop_loss_pct)
                self.position.take_profit = take_profit
                self.position.stop_loss = stop_loss

        elif crossunder(self.data.Close, self.vwap):
            if self.position.is_long:
                self.position.close()
                print(f"🌙 Moon Dev Alert: Closing Long Position (Mean-Reversion) at {self.data.Close[-1]}")
            if not self.position.is_short:
                self.sell(size=position_size)
                print(f"🌙 Moon Dev Alert: Short Entry (Mean-Reversion) at {self.data.Close[-1]}")
                # Set take profit and stop loss
                take_profit = self.data.Close[-1] * (1 - self.take_profit_pct)
                stop_loss = self.data.Close[-1] * (1 + self.stop_loss_pct)
                self.position.take_profit = take_profit
                self.position.stop_loss = stop_loss

        # Trend-Following Setup
        if self.data.Close[-1] > self.vwap[-1]:
            self.consecutive_above += 1
            self.consecutive_below = 0
        else:
            self.consecutive_above = 0

        if self.data.Close[-1] < self.vwap[-1]:
            self.consecutive_below += 1
            self.consecutive_above = 0
        else:
            self.consecutive_below = 0

        if self.consecutive_above >= self.trend_confirmation_candles and not self.position.is_long:
            self.buy(size=position_size)
            print(f"🌙 Moon Dev Alert: Long Entry (Trend-Following) at {self.data.Close[-1]}")
            # Set take profit and stop loss
            take_profit = self.data.Close[-1] * (1 + self.take_profit_pct)
            stop_loss = self.data.Close[-1] * (1 - self.stop_loss_pct)
            self.position.take_profit = take_profit
            self.position.stop_loss = stop_loss

        elif self.consecutive_below >= self.trend_confirmation_candles and not self.position.is_short:
            self.sell(size=position_size)
            print(f"🌙 Moon Dev Alert: Short Entry (Trend-Following) at {self.data.Close[-1]}")
            # Set take profit and stop loss
            take_profit = self.data.Close[-1] * (1 - self.take_profit_pct)
            stop_loss = self.data.Close[-1] * (1 + self.stop_loss_pct)
            self.position.take_profit = take_profit
            self.position.stop_loss = stop_loss

# Load and preprocess data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = preprocess_data(data_path)

# Initialize and run backtest
bt = Backtest(data, VWAPStrategy, cash=1_000_000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)

# Plot initial performance
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    vwap_period=range(10, 50, 5),
    trend_confirmation_candles=range(2, 6),
    take_profit_pct=[0.005, 0.01, 0.015],
    stop_loss_pct=[0.0025, 0.005, 0.0075],
    maximize='Return [%]'
)
print(optimization_results)

# Plot optimized performance
bt.plot()
```

### Explanation of the Code:
1. **Data Preprocessing**:
   - The `preprocess_data` function cleans the column names, drops unnamed columns, and ensures proper column mapping.
   - The datetime column is converted to a datetime object and set as the index.

2. **Strategy Class**:
   - The `VWAPStrategy` class implements the VWAP-based trading strategy.
   - Indicators (VWAP and ATR) are calculated using `talib` functions wrapped in `self.I()`.
   - Entry and exit logic is implemented for both mean-reversion and trend-following setups.
   - Risk management includes position sizing based on a fixed percentage of account equity and setting take profit and stop loss levels.

3. **Backtest Execution**:
   - The backtest is initialized with a cash balance of 1,000,000 and a commission of 0.1%.
   - Initial backtest results are printed and plotted.
   - Parameter optimization is performed using `bt.optimize()`.

4. **Moon Dev Themed Debug Prints**:
   - Entry and exit signals are printed with Moon Dev themed messages for easier debugging.

5. **Optimization**:
   - Parameters such as `vwap_period`, `trend_confirmation_candles`, `take_profit_pct`, and `stop_loss_pct` are optimized to maximize returns.

This implementation provides a robust framework for backtesting and optimizing the VWAP-based trading strategy. 🌙✨🚀