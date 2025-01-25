Here’s the implementation of the Momentum Trading Strategy in Python using `backtesting.py`. The code includes all the necessary components, such as indicators, entry/exit logic, risk management, and parameter optimization. It also includes Moon Dev-themed debug prints for better visualization and debugging.

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, RSI, ATR

# Clean and prepare the data
def prepare_data(data_path):
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

# Momentum Trading Strategy
class MomentumTradingStrategy(Strategy):
    # Strategy parameters
    ema_period = 50
    rsi_period = 14
    atr_period = 14
    atr_multiplier_tp = 1.5
    atr_multiplier_sl = 1.0
    trailing_stop_multiplier = 0.5
    max_trades_per_day = 5
    risk_per_trade = 0.02  # 2% risk per trade

    def init(self):
        # Calculate indicators
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)

        # Track trades per day
        self.trades_today = 0
        self.last_trade_day = None

    def next(self):
        # Reset trades counter at the start of a new day
        if self.last_trade_day != self.data.index[-1].date():
            self.trades_today = 0
            self.last_trade_day = self.data.index[-1].date()

        # Skip if max trades per day reached
        if self.trades_today >= self.max_trades_per_day:
            return

        # Calculate position size based on risk
        atr_value = self.atr[-1]
        sl_distance = atr_value * self.atr_multiplier_sl
        position_size = (self.equity * self.risk_per_trade) / sl_distance

        # Long Entry Logic
        if (self.data.Close[-1] > self.ema[-1] and  # Price above EMA
            50 < self.rsi[-1] < 70 and  # RSI in bullish range
            self.data.Close[-1] > self.data.Open[-1] and  # Bullish candle
            self.trades_today < self.max_trades_per_day):

            # Calculate TP and SL
            tp = self.data.Close[-1] + (atr_value * self.atr_multiplier_tp)
            sl = self.data.Close[-1] - sl_distance

            # Enter long position
            self.buy(size=position_size, sl=sl, tp=tp)
            self.trades_today += 1
            print(f"🌙 Moon Dev Long Entry! 🚀 Price: {self.data.Close[-1]}, TP: {tp}, SL: {sl}")

        # Short Entry Logic
        elif (self.data.Close[-1] < self.ema[-1] and  # Price below EMA
              30 < self.rsi[-1] < 50 and  # RSI in bearish range
              self.data.Close[-1] < self.data.Open[-1] and  # Bearish candle
              self.trades_today < self.max_trades_per_day):

            # Calculate TP and SL
            tp = self.data.Close[-1] - (atr_value * self.atr_multiplier_tp)
            sl = self.data.Close[-1] + sl_distance

            # Enter short position
            self.sell(size=position_size, sl=sl, tp=tp)
            self.trades_today += 1
            print(f"🌙 Moon Dev Short Entry! 🚀 Price: {self.data.Close[-1]}, TP: {tp}, SL: {sl}")

        # Trailing Stop Logic
        for trade in self.trades:
            if trade.is_long:
                trailing_stop = self.data.Close[-1] - (atr_value * self.trailing_stop_multiplier)
                trade.sl = max(trade.sl, trailing_stop)
            elif trade.is_short:
                trailing_stop = self.data.Close[-1] + (atr_value * self.trailing_stop_multiplier)
                trade.sl = min(trade.sl, trailing_stop)

# Load and prepare data
data_path = "{DATA_DIR}/BTC-USD-15m.csv"
data = prepare_data(data_path)

# Run initial backtest
bt = Backtest(data, MomentumTradingStrategy, cash=1_000_000, commission=0.002)
stats = bt.run()
print(stats)
print(stats._strategy)
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    ema_period=range(40, 60, 5),
    rsi_period=range(10, 20, 2),
    atr_multiplier_tp=[1.5, 2.0, 2.5],
    atr_multiplier_sl=[1.0, 1.5],
    maximize='Return [%]'
)
print(optimization_results)
bt.plot()
```

---

### Key Features:
1. **Indicators**:
   - EMA (50-period) for trend direction.
   - RSI (14-period) for momentum.
   - ATR (14-period) for volatility and stop-loss/take-profit levels.

2. **Entry Logic**:
   - Long: Price above EMA, RSI between 50-70, and bullish candle.
   - Short: Price below EMA, RSI between 30-50, and bearish candle.

3. **Exit Logic**:
   - Take profit at 1.5x ATR.
   - Stop loss at 1x ATR.
   - Trailing stop at 0.5x ATR.

4. **Risk Management**:
   - Position sizing based on 2% risk per trade.
   - Maximum of 5 trades per day.

5. **Optimization**:
   - Optimizes EMA period, RSI period, and ATR multipliers.

6. **Moon Dev Debug Prints**:
   - Prints entry signals with emojis for better visualization.

---

### Execution Order:
1. Run the initial backtest with default parameters.
2. Print full stats and strategy details.
3. Show the initial performance plot.
4. Run optimization and display optimized results.
5. Show the final performance plot.

Let me know if you need further adjustments! 🌙✨🚀