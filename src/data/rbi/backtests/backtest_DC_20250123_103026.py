Here’s the implementation of the Swing Trading Strategy in Python using the `backtesting.py` library. The code includes all necessary components, such as indicators, entry/exit logic, risk management, and parameter optimization.

```python
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import SMAIndicator, EMAIndicator
from ta.volume import VolumeWeightedAveragePrice

# 🌙 Moon Dev Debug Print
print("🌙 Initializing Swing Trading Strategy... ✨")

class SwingTradingStrategy(Strategy):
    # Parameters for optimization
    ema_period = 8
    sma_period = 200
    risk_per_trade = 0.02  # 2% risk per trade
    position_size = 1000000  # Fixed position size

    def init(self):
        # 🌙 Moon Dev Debug Print
        print("🌙 Initializing indicators... 🚀")

        # Calculate indicators
        self.ema = self.I(EMAIndicator, self.data.Close, window=self.ema_period).ema_indicator()
        self.sma = self.I(SMAIndicator, self.data.Close, window=self.sma_period).sma_indicator()
        self.vwap = self.I(VolumeWeightedAveragePrice, self.data.High, self.data.Low, self.data.Close, self.data.Volume)

        # 🌙 Moon Dev Debug Print
        print(f"🌙 Indicators initialized: EMA({self.ema_period}), SMA({self.sma_period}), VWAP ✨")

    def next(self):
        # 🌙 Moon Dev Debug Print
        print(f"🌙 Processing candle at {self.data.index[-1]}... 🚀")

        # Check if the stock is above the 200 SMA
        if self.data.Close[-1] < self.sma[-1]:
            print("🌙 Stock is below 200 SMA. Skipping trade. 🛑")
            return

        # Check for breakout above resistance (using VWAP as a proxy for resistance)
        if self.data.Close[-1] > self.vwap[-1] and self.data.Close[-2] <= self.vwap[-2]:
            print("🌙 Breakout detected! Checking for entry near 8 EMA... ✨")

            # Check if the price is near the 8 EMA
            if abs(self.data.Close[-1] - self.ema[-1]) / self.ema[-1] < 0.01:  # Within 1% of the 8 EMA
                print("🌙 Price is near 8 EMA. Entering trade... 🚀")

                # Calculate position size based on risk management
                stop_loss = self.ema[-1]  # Stop loss below the 8 EMA
                risk_amount = self.position_size * self.risk_per_trade
                position_size = risk_amount / (self.data.Close[-1] - stop_loss)

                # Enter the trade
                self.buy(size=position_size, sl=stop_loss)

        # Check for exit conditions
        if self.position:
            print("🌙 Checking exit conditions... ✨")

            # Take partial profits (25% at a time)
            if self.data.Close[-1] > self.position.entry_price * 1.03:  # 3% profit
                print("🌙 Taking partial profits... 🚀")
                self.position.close(0.25)

            # Trail stop loss along the 8 EMA
            if self.data.Close[-1] < self.ema[-1]:
                print("🌙 Price closed below 8 EMA. Exiting trade... 🛑")
                self.position.close()

# Load and preprocess data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# Clean column names and drop unnamed columns
data.columns = data.columns.str.strip().str.lower()
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

# Convert Date column to datetime
data['Date'] = pd.to_datetime(data['Date'])
data = data.set_index('Date')

# 🌙 Moon Dev Debug Print
print("🌙 Data loaded and preprocessed successfully! ✨")

# Run backtest
bt = Backtest(data, SwingTradingStrategy, cash=1000000, commission=0.002)
stats = bt.run()

# 🌙 Moon Dev Debug Print
print("🌙 Backtest complete! Here are the results: 🚀")
print(stats)

# Optimize parameters
optimization_results = bt.optimize(
    ema_period=range(5, 15, 1),
    sma_period=range(150, 250, 10),
    risk_per_trade=[0.01, 0.02, 0.03],
    maximize='Return [%]'
)

# 🌙 Moon Dev Debug Print
print("🌙 Optimization complete! Here are the best parameters: ✨")
print(optimization_results)
```

### Key Features:
1. **Indicators**:
   - 8 EMA for momentum.
   - 200 SMA for long-term trend filtering.
   - VWAP as a proxy for resistance/support levels.

2. **Entry Logic**:
   - Enter trades near the 8 EMA after a breakout above VWAP.
   - Ensure the stock is above the 200 SMA.

3. **Exit Logic**:
   - Take partial profits at 3% gains.
   - Trail stop loss along the 8 EMA.
   - Exit if the price closes below the 8 EMA.

4. **Risk Management**:
   - Risk 2% of capital per trade.
   - Position size calculated based on stop loss distance.

5. **Parameter Optimization**:
   - Optimize EMA period, SMA period, and risk per trade.

6. **Moon Dev Debug Prints**:
   - Added plenty of debug prints with emojis for easier debugging.

Let me know if you need further adjustments! 🌙✨🚀