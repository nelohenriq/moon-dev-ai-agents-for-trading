# Import necessary libraries
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder

# Clean and preprocess data
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

# Define the Swing Trading Strategy
class SwingTradingStrategy(Strategy):
    # Define strategy parameters
    ema_short_period = 8  # 8 EMA
    sma_long_period = 200  # 200 SMA
    risk_per_trade = 0.01  # 1% risk per trade
    take_profit_ratio = 2  # 1:2 risk-reward ratio

    def init(self):
        # Calculate indicators
        self.ema_short = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_short_period)
        self.sma_long = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_long_period)
        self.volume = self.data.Volume

        # Debug prints for Moon Dev 🌙
        print("🌙 Moon Dev Swing Trading Strategy Initialized! 🚀")
        print(f"📊 Indicators: {self.ema_short_period} EMA, {self.sma_long_period} SMA")

    def next(self):
        # Entry logic
        if self.data.Close[-1] > self.sma_long[-1]:  # Stock must be above 200 SMA
            if self.data.Close[-1] > self.ema_short[-1]:  # Stock must be above 8 EMA
                if self.volume[-1] > self.volume[-2]:  # Volume must increase
                    if not self.position:  # No open positions
                        # Calculate position size based on risk
                        stop_loss = self.ema_short[-1]  # Stop loss below 8 EMA
                        risk_amount = self.equity * self.risk_per_trade
                        position_size = risk_amount / (self.data.Close[-1] - stop_loss)
                        position_size = min(position_size, 1000000)  # Cap position size at 1,000,000

                        # Enter long position
                        self.buy(size=position_size, sl=stop_loss)
                        print(f"🚀 Moon Dev Entry Signal! 🌙 Buying at {self.data.Close[-1]} with stop loss at {stop_loss}")

        # Exit logic
        if self.position:
            # Take partial profits at key resistance levels
            if self.data.Close[-1] >= self.position.entry_price * (1 + self.take_profit_ratio * self.risk_per_trade):
                self.position.close(0.25)  # Close 25% of the position
                print(f"🌙 Moon Dev Partial Profit Taken! 🚀 Closing 25% at {self.data.Close[-1]}")

            # Trail stop loss along the 8 EMA
            self.position.sl = max(self.position.sl, self.ema_short[-1])

            # Exit fully if the stock closes below the 8 EMA
            if self.data.Close[-1] < self.ema_short[-1]:
                self.position.close()
                print(f"🌙 Moon Dev Exit Signal! 🚀 Closing position at {self.data.Close[-1]}")

# Run the backtest
bt = Backtest(data, SwingTradingStrategy, cash=1000000, commission=0.002)
stats = bt.run()

# Print full stats
print("🌙 Moon Dev Backtest Results 🚀")
print(stats)
print(stats._strategy)

# Show initial performance plot
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    ema_short_period=range(6, 10, 1),  # Optimize 8 EMA
    sma_long_period=range(190, 210, 5),  # Optimize 200 SMA
    risk_per_trade=[0.01, 0.02],  # Optimize risk per trade
    take_profit_ratio=[2, 3],  # Optimize risk-reward ratio
    maximize='Return [%]'
)

# Print optimized results
print("🌙 Moon Dev Optimized Results 🚀")
print(optimization_results)

# Show optimized performance plot
bt.plot()