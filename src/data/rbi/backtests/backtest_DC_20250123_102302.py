Here’s the implementation of the Swing Trading Strategy in Python using `backtesting.py`. The code includes all necessary components, such as data handling, strategy logic, risk management, and parameter optimization.

```python
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib as ta
from pathlib import Path

# Moon Dev-themed debug prints 🌙✨
def moon_dev_print(message):
    print(f"🌙✨ [Moon Dev] {message}")

# Data handling and cleaning
def load_and_clean_data(filepath):
    moon_dev_print("Loading data... 🚀")
    data = pd.read_csv(filepath)
    
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    moon_dev_print("Cleaned column names 🌟")
    
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    moon_dev_print("Dropped unnamed columns 🗑️")
    
    # Map columns to required format
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    moon_dev_print("Mapped columns to required format 📊")
    
    # Convert datetime column
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    moon_dev_print("Converted datetime and set as index ⏰")
    
    return data

# Strategy class
class SwingTradingStrategy(Strategy):
    # Parameters for optimization
    ema_short_period = 8
    sma_long_period = 200
    risk_per_trade = 0.02  # Risk 2% of account per trade

    def init(self):
        # Calculate indicators
        self.ema_short = self.I(ta.EMA, self.data.Close, self.ema_short_period)
        self.sma_long = self.I(ta.SMA, self.data.Close, self.sma_long_period)
        moon_dev_print("Indicators initialized 📈")

    def next(self):
        # Entry logic
        if not self.position:
            # Check if price is above 200 SMA and breaks above resistance (8 EMA)
            if self.data.Close[-1] > self.sma_long[-1] and crossover(self.data.Close, self.ema_short):
                # Calculate position size based on risk management
                stop_loss_price = self.ema_short[-1]  # Stop loss below 8 EMA
                risk_per_share = self.data.Close[-1] - stop_loss_price
                position_size = (self.equity * self.risk_per_trade) / risk_per_share
                position_size = int(position_size)
                
                # Enter trade
                self.buy(size=position_size)
                moon_dev_print(f"Entered trade at {self.data.Close[-1]} 🟢")

        # Exit logic
        elif self.position:
            # Take partial profits (25% at a time)
            if self.data.Close[-1] > self.position.entry_price * 1.05:  # 5% profit
                self.sell(size=int(self.position.size * 0.25))
                moon_dev_print(f"Took partial profit at {self.data.Close[-1]} 💰")

            # Exit fully if price closes below 8 EMA
            if self.data.Close[-1] < self.ema_short[-1]:
                self.position.close()
                moon_dev_print(f"Exited trade at {self.data.Close[-1]} 🔴")

# Load and clean data
data_path = Path("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")
data = load_and_clean_data(data_path)

# Backtest setup
bt = Backtest(data, SwingTradingStrategy, cash=10000, commission=0.001)
moon_dev_print("Backtest initialized 🧪")

# Run backtest
results = bt.run()
moon_dev_print("Backtest completed 🎉")
print(results)

# Optimize parameters
moon_dev_print("Optimizing parameters... 🔍")
optimization_results = bt.optimize(
    ema_short_period=range(5, 15, 1),
    sma_long_period=range(150, 250, 10),
    risk_per_trade=[0.01, 0.02, 0.03],
    maximize='Return [%]'
)
moon_dev_print("Optimization completed 🏆")
print(optimization_results)
```

---

### Explanation of the Code:

1. **Data Handling**:
   - The `load_and_clean_data` function ensures the data is properly formatted and cleaned.
   - Column names are standardized, and unnecessary columns are dropped.

2. **Strategy Class**:
   - The `SwingTradingStrategy` class implements the strategy logic.
   - Indicators (8 EMA and 200 SMA) are calculated using `talib`.
   - Entry logic checks for breakouts above the 8 EMA and ensures the price is above the 200 SMA.
   - Exit logic includes partial profit-taking and a stop loss below the 8 EMA.

3. **Risk Management**:
   - Position size is calculated based on the risk per trade (2% of account equity).
   - Stop loss is set below the 8 EMA.

4. **Backtesting**:
   - The `Backtest` class from `backtesting.py` is used to simulate the strategy.
   - Results are printed, including key metrics like return, win rate, and drawdown.

5. **Parameter Optimization**:
   - The `optimize` method is used to find the best parameters for the strategy.
   - Parameters like `ema_short_period`, `sma_long_period`, and `risk_per_trade` are optimized.

---

### Moon Dev Debug Prints 🌙✨:
- Debug prints are added throughout the code to make it easier to track the flow of execution.
- These prints include emojis for better readability and fun! 🚀

---

### Next Steps:
1. Run the backtest on your dataset.
2. Analyze the results and refine the strategy as needed.
3. Use the optimized parameters for live trading.

Happy backtesting! 🌙✨