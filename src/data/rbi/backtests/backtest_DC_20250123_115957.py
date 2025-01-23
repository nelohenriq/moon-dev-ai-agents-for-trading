Here’s the implementation of the VWAP-based trading strategy in Python using the `backtesting.py` framework. The code includes all the necessary components, such as indicators, entry/exit logic, risk management, and parameter optimization.

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder
from backtesting.test import SMA

# Clean and prepare the data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")
data.columns = data.columns.str.strip().str.lower()  # Clean column names
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])  # Drop unnamed columns

# Map columns to required format
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Ensure datetime is in the correct format
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class VWAPStrategy(Strategy):
    # Strategy parameters
    vwap_period = 20  # VWAP period
    atr_period = 14  # ATR period for stop loss and take profit
    volume_threshold = 1.2  # Volume threshold multiplier
    risk_per_trade = 0.01  # Risk 1% of account per trade
    rr_ratio = 2  # Risk-reward ratio

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume, timeperiod=self.vwap_period)
        
        # Calculate ATR for stop loss and take profit
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        # Calculate average volume for filtering
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=self.vwap_period)
        
        # Debug prints
        print("🌙 Moon Dev Strategy Initialized! 🚀")
        print(f"VWAP Period: {self.vwap_period}, ATR Period: {self.atr_period}, Volume Threshold: {self.volume_threshold}")

    def next(self):
        # Skip if indicators are not ready
        if len(self.data) < self.vwap_period or len(self.data) < self.atr_period:
            return

        # Current price and indicators
        price = self.data.Close[-1]
        vwap = self.vwap[-1]
        atr = self.atr[-1]
        volume = self.data.Volume[-1]
        avg_volume = self.avg_volume[-1]

        # Position sizing based on risk management
        position_size = (self.equity * self.risk_per_trade) / (atr * self.rr_ratio)

        # Entry logic
        if not self.position:
            # Mean-reversion entry
            if crossover(price, vwap) and volume > avg_volume * self.volume_threshold:
                self.buy(size=position_size, sl=price - atr, tp=price + atr * self.rr_ratio)
                print(f"🌙 Buy Signal! Price: {price}, VWAP: {vwap}, Volume: {volume} 🚀")
            elif crossunder(price, vwap) and volume > avg_volume * self.volume_threshold:
                self.sell(size=position_size, sl=price + atr, tp=price - atr * self.rr_ratio)
                print(f"🌙 Sell Signal! Price: {price}, VWAP: {vwap}, Volume: {volume} 🚀")

        # Exit logic
        if self.position:
            if self.position.is_long and crossunder(price, vwap):
                self.position.close()
                print(f"🌙 Exit Long! Price: {price}, VWAP: {vwap} 🚀")
            elif self.position.is_short and crossover(price, vwap):
                self.position.close()
                print(f"🌙 Exit Short! Price: {price}, VWAP: {vwap} 🚀")

# Backtest execution
bt = Backtest(data, VWAPStrategy, cash=1_000_000, commission=0.001)

# Initial backtest with default parameters
stats = bt.run()
print(stats)
print(stats._strategy)

# Show initial performance plot
bt.plot()

# Optimization
optimization_results = bt.optimize(
    vwap_period=range(10, 50, 5),
    atr_period=range(10, 20, 2),
    volume_threshold=[1.1, 1.2, 1.3],
    rr_ratio=[1.5, 2, 2.5],
    maximize='Return [%]'
)

# Show optimized results
print(optimization_results)

# Final backtest with optimized parameters
optimized_stats = bt.run(**optimization_results._strategy_params)
print(optimized_stats)
print(optimized_stats._strategy)

# Show final performance plot
bt.plot()
```

---

### Explanation of the Code:

1. **Data Preparation**:
   - The data is cleaned and mapped to the required format (`Open`, `High`, `Low`, `Close`, `Volume`).
   - Unnamed columns are dropped, and the datetime column is set as the index.

2. **Strategy Class**:
   - The `VWAPStrategy` class implements the VWAP-based trading strategy.
   - Indicators (VWAP, ATR, and average volume) are calculated using `talib` and wrapped in `self.I()`.
   - Entry and exit logic is based on price interaction with VWAP, volume filtering, and ATR-based stop loss/take profit.

3. **Risk Management**:
   - Position size is calculated based on 1% risk per trade and the ATR-based stop loss.
   - A risk-reward ratio is used to set take profit levels.

4. **Backtest Execution**:
   - The initial backtest is run with default parameters.
   - Optimization is performed on key parameters (`vwap_period`, `atr_period`, `volume_threshold`, `rr_ratio`).
   - The optimized results are printed, and the final backtest is run with the best parameters.

5. **Moon Dev Debug Prints**:
   - Debug prints are added to track entry/exit signals and strategy initialization.

---

### Output:
- Initial backtest statistics and performance plot.
- Optimized parameters and final backtest statistics.
- Final performance plot with optimized parameters.

Let me know if you need further refinements! 🌙✨🚀