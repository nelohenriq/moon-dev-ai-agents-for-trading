Below is the Python implementation of the swing trading strategy using the `backtesting.py` library. The code includes all necessary imports, the strategy class with indicators, entry/exit logic, risk management, and parameter optimization.

```python
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import EMAIndicator, SMAIndicator
from ta.volume import VolumeWeightedAveragePrice

# Load data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['datetime'])
data.set_index('datetime', inplace=True)
data.columns = [col.lower() for col in data.columns]  # Ensure lowercase column names

class SwingTradingStrategy(Strategy):
    # Parameters for optimization
    ema_period = 8
    sma_period = 200
    risk_per_trade = 0.02  # Risk 2% of capital per trade
    take_profit_pct = 0.25  # Take profit in 25% increments

    def init(self):
        # Calculate indicators
        self.ema = self.I(EMAIndicator, self.data.close, self.ema_period).ema_indicator()
        self.sma = self.I(SMAIndicator, self.data.close, self.sma_period).sma_indicator()
        self.vwap = self.I(VolumeWeightedAveragePrice, self.data.high, self.data.low, self.data.close, self.data.volume).volume_weighted_average_price()

    def next(self):
        # Entry logic
        if not self.position:
            # Check if price is above 200 SMA and trending along 8 EMA
            if self.data.close[-1] > self.sma[-1] and self.data.close[-1] > self.ema[-1]:
                # Look for breakout above resistance with volume confirmation
                if self.data.close[-1] > self.data.high[-2] and self.data.volume[-1] > self.data.volume[-2]:
                    # Calculate position size based on risk management
                    stop_loss_level = self.ema[-1]  # Stop loss below 8 EMA
                    risk_amount = self.equity * self.risk_per_trade
                    position_size = risk_amount / (self.data.close[-1] - stop_loss_level)
                    self.buy(size=position_size)

        # Exit logic
        if self.position:
            # Take profit in partial sizes
            if self.data.close[-1] > self.position.entry_price * (1 + self.take_profit_pct):
                self.sell(size=self.position.size * 0.25)  # Sell 25% of position
            # Trail stop loss along 8 EMA
            if self.data.close[-1] < self.ema[-1]:
                self.position.close()  # Exit if price closes below 8 EMA

# Backtest setup
bt = Backtest(data, SwingTradingStrategy, cash=10000, commission=0.001)

# Run backtest
stats = bt.run()
print(stats)

# Optimization
optimization_results = bt.optimize(
    ema_period=range(5, 15),
    sma_period=range(100, 300, 50),
    risk_per_trade=[0.01, 0.02, 0.03],
    take_profit_pct=[0.2, 0.25, 0.3],
    maximize='Return [%]'
)
print(optimization_results)

# Plot results
bt.plot()
```

### Explanation of the Code:
1. **Imports**:
   - `pandas` and `numpy` for data manipulation.
   - `backtesting` library for backtesting and strategy implementation.
   - `ta` library for technical indicators (EMA, SMA, VWAP).

2. **Data Loading**:
   - Loads the BTC-USD 15-minute data from the specified path.
   - Ensures the `datetime` column is parsed and set as the index.

3. **Strategy Class**:
   - Defines the `SwingTradingStrategy` class with parameters for EMA, SMA, risk per trade, and take profit percentage.
   - Initializes indicators (8 EMA, 200 SMA, VWAP) in the `init` method.
   - Implements entry and exit logic in the `next` method:
     - Enters a trade if the price is above the 200 SMA and 8 EMA, with a breakout confirmed by volume.
     - Exits partially at 25% profit increments and fully if the price closes below the 8 EMA.

4. **Risk Management**:
   - Position sizing is calculated based on the risk per trade (2% of equity) and the distance between entry price and stop loss (8 EMA).

5. **Backtest Execution**:
   - Runs the backtest with $10,000 initial capital and a 0.1% commission.
   - Prints performance statistics.

6. **Parameter Optimization**:
   - Optimizes the EMA period, SMA period, risk per trade, and take profit percentage to maximize return.

7. **Plotting**:
   - Plots the backtest results for visual analysis.

### Key Metrics Tracked:
- **Win Rate**: Percentage of winning trades.
- **Average Profit/Loss**: Average profit and loss per trade.
- **Risk-Reward Ratio**: Ratio of average profit to average loss.
- **Maximum Drawdown**: Largest peak-to-trough decline in equity.

### Notes:
- The strategy is designed for daily charts but can be adapted to other timeframes.
- Ensure the data includes sufficient historical data (1-2 years) for robust backtesting.
- Regularly review and refine the strategy based on backtest results.