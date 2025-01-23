Here’s the implementation of the Swing Trading Strategy in Python using the `backtesting.py` library. The code includes all necessary components, such as indicators, entry/exit logic, risk management, and parameter optimization.

```python
# 🌙 Moon Dev's Swing Trading Strategy Backtest 🌙
# 🚀 Let's get started! 🚀

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import SMAIndicator, EMAIndicator
from ta.volume import VolumeWeightedAveragePrice

# 🌙 Data Cleaning and Preparation 🌙
def prepare_data(data_path):
    # Load data
    data = pd.read_csv(data_path)
    
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Map columns to required format
    data = data.rename(columns={
        'datetime': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Ensure proper datetime format
    data['Date'] = pd.to_datetime(data['Date'])
    data = data.set_index('Date')
    
    return data

# 🌙 Strategy Class 🌙
class SwingTradingStrategy(Strategy):
    # Parameters for optimization
    ema_period = 8
    sma_period = 200
    risk_per_trade = 0.01  # Risk 1% of account per trade
    
    def init(self):
        # Calculate indicators
        self.ema = self.I(EMAIndicator, self.data.Close, self.ema_period)
        self.sma = self.I(SMAIndicator, self.data.Close, self.sma_period)
        self.vwap = self.I(VolumeWeightedAveragePrice, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        
        # Debug prints 🌙
        print("🌙 Indicators initialized! 🌙")
        print(f"EMA Period: {self.ema_period}, SMA Period: {self.sma_period}")
    
    def next(self):
        # Entry Logic
        if self.data.Close[-1] > self.sma[-1]:  # Only trade above 200 SMA
            if crossover(self.data.Close, self.ema):  # Breakout above 8 EMA
                if self.data.Volume[-1] > self.data.Volume.mean():  # Volume confirmation
                    # Calculate position size based on risk management
                    stop_loss = self.ema[-1] * 0.99  # Stop loss below 8 EMA
                    risk_amount = self.equity * self.risk_per_trade
                    position_size = risk_amount / (self.data.Close[-1] - stop_loss)
                    
                    # Enter trade
                    self.buy(size=position_size, sl=stop_loss)
                    print(f"🌙 Entered Long at {self.data.Close[-1]} 🌙")
        
        # Exit Logic
        for trade in self.trades:
            if trade.is_long:
                # Take partial profits
                if self.data.Close[-1] >= trade.entry_price * 1.03:  # 3% profit
                    self.sell(size=trade.size * 0.25)
                    print(f"🌙 Took 25% Profit at {self.data.Close[-1]} 🌙")
                
                # Trail stop loss along 8 EMA
                if self.data.Close[-1] < self.ema[-1]:
                    self.sell()
                    print(f"🌙 Exited Long at {self.data.Close[-1]} 🌙")

# 🌙 Backtest Execution 🌙
if __name__ == "__main__":
    # Load and prepare data
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    data = prepare_data(data_path)
    
    # Initialize backtest
    bt = Backtest(data, SwingTradingStrategy, cash=1_000_000, commission=0.001)
    
    # Run backtest
    stats = bt.run()
    print("🌙 Backtest Results 🌙")
    print(stats)
    
    # Optimize parameters
    optimization_results = bt.optimize(
        ema_period=range(6, 10, 1),
        sma_period=range(180, 220, 10),
        maximize='Return [%]'
    )
    print("🌙 Optimization Results 🌙")
    print(optimization_results)
    
    # Plot results
    bt.plot()
```

---

### Key Features of the Code:
1. **Data Preparation**:
   - Cleans column names and removes unnamed columns.
   - Maps columns to the required format (`Open`, `High`, `Low`, `Close`, `Volume`).
   - Converts the `datetime` column to a proper datetime format.

2. **Strategy Logic**:
   - Uses **8 EMA** for momentum and **200 SMA** for trend filtering.
   - Confirms breakouts with **volume**.
   - Implements **risk management** by risking 1% of the account per trade.
   - Takes partial profits and trails stop loss along the 8 EMA.

3. **Backtesting**:
   - Runs the backtest with a starting capital of **1,000,000**.
   - Optimizes parameters (`ema_period` and `sma_period`) for maximum return.

4. **Debug Prints**:
   - Includes Moon Dev-themed debug prints for easy tracking of trades and indicators.

5. **Visualization**:
   - Plots the backtest results for visual analysis.

---

### How to Use:
1. Replace the `data_path` with your dataset location.
2. Run the script to backtest the strategy.
3. Analyze the results and optimize parameters as needed.

---

### Moon Dev Debugging Tips 🌙:
- Look for the 🌙 emoji in the console to track trades and debug prints.
- Use the optimization results to fine-tune the strategy for better performance.
- Always review the equity curve and metrics to ensure the strategy aligns with your goals.

Happy backtesting! 🚀✨