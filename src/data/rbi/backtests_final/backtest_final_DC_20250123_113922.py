# Import necessary libraries
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

# Clean and prepare the data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")

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

# Ensure proper datetime format
data['Date'] = pd.to_datetime(data['Date'])
data.set_index('Date', inplace=True)

# Strategy class
class VWAPVolumeRSI(Strategy):
    # Define strategy parameters
    rsi_period = 14
    volume_sma_period = 20
    risk_per_trade = 0.01  # Risk 1% of capital per trade
    risk_reward_ratio = 2  # Risk-reward ratio of 1:2

    def init(self):
        # Calculate indicators
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.volume_sma_period)

        # Debug prints
        print("🌙 Moon Dev Strategy Initialized! 🚀")
        print(f"RSI Period: {self.rsi_period}, Volume SMA Period: {self.volume_sma_period}")

    def next(self):
        # Calculate position size based on risk management
        position_size = self.equity * self.risk_per_trade / self.data.Close[-1]

        # Long entry conditions
        if (self.data.Close[-1] > self.vwap[-1] and
            self.data.Volume[-1] > self.volume_sma[-1] and
            self.rsi[-1] < 50 and self.rsi[-1] > self.rsi[-2]):
            self.buy(size=position_size)
            print(f"🌙 Long Entry Signal! 🚀 Price: {self.data.Close[-1]}, RSI: {self.rsi[-1]}")

        # Short entry conditions
        elif (self.data.Close[-1] < self.vwap[-1] and
              self.data.Volume[-1] > self.volume_sma[-1] and
              self.rsi[-1] > 50 and self.rsi[-1] < self.rsi[-2]):
            self.sell(size=position_size)
            print(f"🌙 Short Entry Signal! 🚀 Price: {self.data.Close[-1]}, RSI: {self.rsi[-1]}")

        # Exit conditions for long positions
        for trade in self.trades:
            if trade.is_long:
                if self.rsi[-1] > 70 or self.data.Close[-1] >= trade.entry_price * (1 + self.risk_reward_ratio * self.risk_per_trade):
                    trade.close()
                    print(f"🌙 Long Exit Signal! 🚀 Price: {self.data.Close[-1]}, RSI: {self.rsi[-1]}")

            # Exit conditions for short positions
            elif trade.is_short:
                if self.rsi[-1] < 30 or self.data.Close[-1] <= trade.entry_price * (1 - self.risk_reward_ratio * self.risk_per_trade):
                    trade.close()
                    print(f"🌙 Short Exit Signal! 🚀 Price: {self.data.Close[-1]}, RSI: {self.rsi[-1]}")

# Run initial backtest
bt = Backtest(data, VWAPVolumeRSI, cash=1_000_000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)

# Show initial performance plot
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    rsi_period=range(10, 20, 2),
    volume_sma_period=range(15, 25, 2),
    maximize='Return [%]',
    constraint=lambda p: p.rsi_period < p.volume_sma_period  # Ensure RSI period < Volume SMA period
)

# Print optimized results
print("🌙 Optimized Results 🚀")
print(optimization_results)

# Show optimized performance plot
bt.plot()