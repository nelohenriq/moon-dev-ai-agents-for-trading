import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Clean and preprocess data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")
data.columns = data.columns.str.strip().str.lower()  # Clean column names
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])  # Drop unnamed columns
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)  # Map columns to required format
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# Strategy class
class VWAPStrategy(Strategy):
    # Parameters for optimization
    vwap_deviation = 1.5  # Percentage deviation from VWAP for mean-reversion
    rsi_period = 14  # RSI period for overbought/oversold conditions
    atr_period = 14  # ATR period for stop-loss
    risk_per_trade = 0.01  # Risk 1% of account per trade
    reward_ratio = 2  # Risk-reward ratio

    def init(self):
        # Calculate indicators
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)

        # Debug prints
        print("🌙 Moon Dev Strategy Initialized! ✨")
        print(f"VWAP Deviation: {self.vwap_deviation}%")
        print(f"RSI Period: {self.rsi_period}")
        print(f"ATR Period: {self.atr_period}")

    def next(self):
        # Calculate price deviation from VWAP
        price_deviation = (self.data.Close[-1] - self.vwap[-1]) / self.vwap[-1] * 100

        # Mean-reversion logic
        if price_deviation > self.vwap_deviation and self.rsi[-1] > 70:  # Overbought condition
            self.sell(size=self.position_size(), sl=self.stop_loss(), tp=self.take_profit())
            print(f"🚀 Short Entry: Price {self.data.Close[-1]} is {price_deviation:.2f}% above VWAP 🌙")
        elif price_deviation < -self.vwap_deviation and self.rsi[-1] < 30:  # Oversold condition
            self.buy(size=self.position_size(), sl=self.stop_loss(), tp=self.take_profit())
            print(f"🚀 Long Entry: Price {self.data.Close[-1]} is {abs(price_deviation):.2f}% below VWAP 🌙")

        # Trend-following logic
        if crossover(self.data.Close, self.vwap) and self.rsi[-1] > 50:  # Bullish crossover
            self.buy(size=self.position_size(), sl=self.stop_loss(), tp=self.take_profit())
            print(f"🚀 Trend-Following Long Entry: Price crossed above VWAP 🌙")
        elif crossover(self.vwap, self.data.Close) and self.rsi[-1] < 50:  # Bearish crossover
            self.sell(size=self.position_size(), sl=self.stop_loss(), tp=self.take_profit())
            print(f"🚀 Trend-Following Short Entry: Price crossed below VWAP 🌙")

    def position_size(self):
        # Calculate position size based on risk percentage
        account_size = self.equity
        risk_amount = account_size * self.risk_per_trade
        stop_loss_distance = abs(self.data.Close[-1] - self.stop_loss())
        return risk_amount / stop_loss_distance if stop_loss_distance != 0 else 0

    def stop_loss(self):
        # Dynamic stop-loss based on ATR
        if self.position.is_long:
            return self.data.Close[-1] - 1.5 * self.atr[-1]
        else:
            return self.data.Close[-1] + 1.5 * self.atr[-1]

    def take_profit(self):
        # Take profit based on risk-reward ratio
        if self.position.is_long:
            return self.data.Close[-1] + self.reward_ratio * abs(self.data.Close[-1] - self.stop_loss())
        else:
            return self.data.Close[-1] - self.reward_ratio * abs(self.data.Close[-1] - self.stop_loss())

# Backtest execution
bt = Backtest(data, VWAPStrategy, cash=1_000_000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)
bt.plot()

# Parameter optimization
optimization_results = bt.optimize(
    vwap_deviation=range(10, 30, 5),  # Test VWAP deviation from 1% to 3%
    rsi_period=range(10, 20, 2),  # Test RSI periods
    atr_period=range(10, 20, 2),  # Test ATR periods
    maximize='Return [%]'
)
print(optimization_results)
bt.plot()