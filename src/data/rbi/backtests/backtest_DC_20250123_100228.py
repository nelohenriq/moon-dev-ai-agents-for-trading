Below is the Python implementation of the swing trading strategy using the `backtesting.py` library. The code includes all necessary imports, the strategy class with indicators, entry/exit logic, risk management, and parameter optimization.

```python
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib as ta
import pandas_ta as pta

# Load data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['Date'])
data.set_index('Date', inplace=True)

# Define the Swing Trading Strategy
class SwingTradingStrategy(Strategy):
    # Parameters for optimization
    ema_short_period = 8
    sma_long_period = 200
    risk_per_trade = 0.02  # 2% risk per trade

    def init(self):
        # Calculate indicators
        self.ema_short = self.I(ta.EMA, self.data.Close, self.ema_short_period)
        self.sma_long = self.I(ta.SMA, self.data.Close, self.sma_long_period)
        self.volume = self.data.Volume

    def next(self):
        # Entry logic
        if not self.position:
            # Long entry: Price above 200 SMA, breaks above resistance (8 EMA), and volume confirms
            if (self.data.Close[-1] > self.sma_long[-1] and
                crossover(self.data.Close, self.ema_short) and
                self.volume[-1] > self.volume.mean()):
                
                # Calculate position size based on risk management
                stop_loss_price = self.ema_short[-1]
                risk_amount = self.equity * self.risk_per_trade
                position_size = risk_amount / (self.data.Close[-1] - stop_loss_price)
                
                # Enter long position
                self.buy(size=position_size, sl=stop_loss_price)

        # Exit logic
        elif self.position.is_long:
            # Trailing stop: Exit if price closes below 8 EMA
            if self.data.Close[-1] < self.ema_short[-1]:
                self.position.close()

            # Partial take profit: Sell 25% at first breakout, 25% at next resistance, trail the rest
            if len(self.trades) == 1:  # First breakout
                self.sell(size=0.25 * self.position.size)
            elif len(self.trades) == 2:  # Next resistance
                self.sell(size=0.25 * self.position.size)
            else:
                # Trail the remaining 50% along the 8 EMA
                self.position.sl = self.ema_short[-1]

# Backtest setup
bt = Backtest(data, SwingTradingStrategy, cash=10000, commission=0.001)

# Run backtest
stats = bt.run()
print(stats)

# Optimize parameters
optimization_results = bt.optimize(
    ema_short_period=range(5, 15),
    sma_long_period=range(100, 300, 50),
    risk_per_trade=[0.01, 0.02, 0.03],
    maximize='Return [%]'
)
print(optimization_results)

# Plot the results
bt.plot()
```

---

### Explanation of the Code:

1. **Imports**:
   - `pandas` and `numpy` for data manipulation.
   - `backtesting` library for backtesting and strategy implementation.
   - `talib` and `pandas_ta` for technical indicators.

2. **Data Loading**:
   - The data is loaded from the specified CSV file and indexed by the `Date` column.

3. **Strategy Class**:
   - The `SwingTradingStrategy` class inherits from `backtesting.Strategy`.
   - Indicators (`8 EMA`, `200 SMA`, and `Volume`) are calculated in the `init` method.
   - Entry and exit logic is implemented in the `next` method.

4. **Entry Logic**:
   - A long position is entered if:
     - The price is above the 200 SMA.
     - The price crosses above the 8 EMA.
     - Volume is above the average volume.

5. **Risk Management**:
   - Position size is calculated based on a 2% risk per trade.
   - A stop loss is placed below the 8 EMA.

6. **Exit Logic**:
   - Partial take profits are taken at 25% increments.
   - The remaining position is trailed along the 8 EMA.

7. **Backtest Execution**:
   - The backtest is run with an initial cash balance of $10,000 and a commission of 0.1%.

8. **Parameter Optimization**:
   - The strategy is optimized for the `ema_short_period`, `sma_long_period`, and `risk_per_trade` parameters.

9. **Results**:
   - The backtest results are printed, and the optimization results are displayed.
   - A plot of the backtest is generated for visualization.

---

### Notes:
- Replace the data path with your actual data file path.
- Adjust the `risk_per_trade` parameter based on your risk tolerance.
- The optimization step can be customized to focus on specific metrics (e.g., Sharpe ratio, win rate, etc.).
- Ensure you have the required libraries installed (`backtesting`, `talib`, `pandas_ta`).