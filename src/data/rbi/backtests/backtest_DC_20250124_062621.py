Here’s the implementation of the backtest for your strategy using `backtesting.py`. The code includes all the necessary components, such as trend identification, momentum confirmation, volatility filtering, entry/exit rules, and risk management. It also includes Moon Dev-themed debug prints for easier debugging and tracking.

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Moon Dev-themed debug prints 🌙✨
def moon_dev_print(message):
    print(f"🌙✨ [Moon Dev] {message}")

class TrendMomentumATRStrategy(Strategy):
    # Strategy parameters
    sma_short_period = 50
    sma_long_period = 200
    rsi_period = 14
    atr_period = 14
    atr_multiplier = 1.5
    risk_per_trade = 0.01  # 1% risk per trade
    max_drawdown = 0.10  # 10% max drawdown
    take_profit_multiplier = 2
    stop_loss_multiplier = 1

    def init(self):
        # Clean and prepare data
        self.data.columns = self.data.columns.str.strip().str.lower()
        self.data = self.data.drop(columns=[col for col in self.data.columns if 'unnamed' in col.lower()])

        # Calculate indicators
        self.sma_short = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_short_period)
        self.sma_long = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_long_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)

        # Track entry ATR for stop-loss and take-profit calculations
        self.entry_atr = None

    def next(self):
        # Check for max drawdown
        if self.equity < self.initial_cash * (1 - self.max_drawdown):
            moon_dev_print("Max drawdown reached! Stopping trading. 🌧️")
            self.position.close()
            return

        # Long entry conditions
        if (self.sma_short[-1] > self.sma_long[-1] and  # Trend condition
            self.rsi[-1] > 50 and self.rsi[-1] < 70 and  # Momentum condition
            self.atr[-1] > self.atr_multiplier * self.atr.mean() and  # Volatility condition
            self.data.Close[-1] > self.sma_short[-1]):  # Price action
            if not self.position.is_long:
                self.entry_atr = self.atr[-1]
                risk_amount = self.equity * self.risk_per_trade
                position_size = risk_amount / (self.entry_atr * self.stop_loss_multiplier)
                self.buy(size=position_size)
                moon_dev_print(f"Long entry! 🌕 Position size: {position_size:.2f}")

        # Short entry conditions
        elif (self.sma_short[-1] < self.sma_long[-1] and  # Trend condition
              self.rsi[-1] < 50 and self.rsi[-1] > 30 and  # Momentum condition
              self.atr[-1] > self.atr_multiplier * self.atr.mean() and  # Volatility condition
              self.data.Close[-1] < self.sma_short[-1]):  # Price action
            if not self.position.is_short:
                self.entry_atr = self.atr[-1]
                risk_amount = self.equity * self.risk_per_trade
                position_size = risk_amount / (self.entry_atr * self.stop_loss_multiplier)
                self.sell(size=position_size)
                moon_dev_print(f"Short entry! 🌑 Position size: {position_size:.2f}")

        # Exit logic for long positions
        if self.position.is_long:
            take_profit = self.position.entry_price + self.entry_atr * self.take_profit_multiplier
            stop_loss = self.position.entry_price - self.entry_atr * self.stop_loss_multiplier
            trailing_stop = self.data.Close[-1] - self.entry_atr * self.stop_loss_multiplier

            if self.data.Close[-1] >= take_profit:
                self.position.close()
                moon_dev_print("Take profit hit! 🎯")
            elif self.data.Close[-1] <= stop_loss:
                self.position.close()
                moon_dev_print("Stop loss hit! 🛑")
            elif self.data.Close[-1] < trailing_stop:
                self.position.close()
                moon_dev_print("Trailing stop hit! 🚦")

        # Exit logic for short positions
        if self.position.is_short:
            take_profit = self.position.entry_price - self.entry_atr * self.take_profit_multiplier
            stop_loss = self.position.entry_price + self.entry_atr * self.stop_loss_multiplier
            trailing_stop = self.data.Close[-1] + self.entry_atr * self.stop_loss_multiplier

            if self.data.Close[-1] <= take_profit:
                self.position.close()
                moon_dev_print("Take profit hit! 🎯")
            elif self.data.Close[-1] >= stop_loss:
                self.position.close()
                moon_dev_print("Stop loss hit! 🛑")
            elif self.data.Close[-1] > trailing_stop:
                self.position.close()
                moon_dev_print("Trailing stop hit! 🚦")

# Load data
data_path = "{DATA_DIR}/BTC-USD-15m.csv"
data = pd.read_csv(data_path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# Run initial backtest
bt = Backtest(data, TrendMomentumATRStrategy, cash=1000000, commission=0.001, margin=1.0)
stats = bt.run()
print(stats)
print(stats._strategy)
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    sma_short_period=range(40, 60, 5),
    sma_long_period=range(190, 210, 5),
    atr_multiplier=[1.0, 1.5, 2.0],
    take_profit_multiplier=[1.5, 2.0, 2.5],
    stop_loss_multiplier=[0.5, 1.0, 1.5],
    maximize='Sharpe Ratio'
)
print(optimization_results)
bt.plot()
```

### Explanation of the Code:
1. **Imports**: Includes necessary libraries like `pandas`, `talib`, and `backtesting`.
2. **Data Preparation**: Cleans column names, drops unnamed columns, and ensures proper column mapping.
3. **Strategy Class**:
   - **Indicators**: Calculates SMA, RSI, and ATR using `talib`.
   - **Entry Logic**: Combines trend, momentum, and volatility conditions for long and short entries.
   - **Exit Logic**: Uses take-profit, stop-loss, and trailing stops based on ATR.
   - **Risk Management**: Limits risk to 1% per trade and enforces a maximum drawdown of 10%.
4. **Backtest Execution**:
   - Runs an initial backtest with default parameters.
   - Prints full stats and plots the performance.
   - Optimizes parameters using ranges for SMA periods, ATR multiplier, and risk-reward ratios.
5. **Moon Dev Debug Prints**: Adds themed debug messages for easier tracking of trades and strategy behavior.

### Next Steps:
1. Run the backtest with your data.
2. Analyze the results and adjust parameters as needed.
3. Use the optimized parameters for live trading or further testing.

Let me know if you need further assistance! 🌙✨