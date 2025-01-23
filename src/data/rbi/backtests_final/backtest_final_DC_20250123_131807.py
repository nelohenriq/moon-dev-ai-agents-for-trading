# Import necessary libraries
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Clean and prepare the data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")

# Clean column names and drop unnamed columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Convert datetime column to proper format
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

# Define the VWAP-based strategy
class VWAPStrategy(Strategy):
    # Strategy parameters
    risk_per_trade = 0.01  # Risk 1% of the account per trade
    profit_target = 0.02  # 2% profit target
    stop_loss = 0.01  # 1% stop loss

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(self.calculate_vwap, self.data.Close, self.data.Volume)
        print("🌙 VWAP Indicator Initialized! ✨")

    def calculate_vwap(self, close, volume):
        # Calculate VWAP using the formula: sum(price * volume) / sum(volume)
        cumulative_price_volume = (close * volume).cumsum()
        cumulative_volume = volume.cumsum()
        vwap = cumulative_price_volume / cumulative_volume
        return vwap

    def next(self):
        # Entry logic
        if crossover(self.data.Close, self.vwap):  # Price crosses above VWAP
            if not self.position:
                self.buy(sl=self.data.Close[-1] * (1 - self.stop_loss), 
                         tp=self.data.Close[-1] * (1 + self.profit_target))
                print(f"🚀 Moon Dev Buy Signal! Entering Long at {self.data.Close[-1]} ✨")
        elif crossover(self.vwap, self.data.Close):  # Price crosses below VWAP
            if not self.position:
                self.sell(sl=self.data.Close[-1] * (1 + self.stop_loss), 
                          tp=self.data.Close[-1] * (1 - self.profit_target))
                print(f"🌙 Moon Dev Sell Signal! Entering Short at {self.data.Close[-1]} ✨")

        # Exit logic
        if self.position:
            if self.position.is_long and crossover(self.vwap, self.data.Close):  # Exit long
                self.position.close()
                print(f"🌙 Moon Dev Exit Signal! Closing Long at {self.data.Close[-1]} ✨")
            elif self.position.is_short and crossover(self.data.Close, self.vwap):  # Exit short
                self.position.close()
                print(f"🌙 Moon Dev Exit Signal! Closing Short at {self.data.Close[-1]} ✨")

# Run the backtest
bt = Backtest(data, VWAPStrategy, cash=1_000_000, commission=0.002)
stats = bt.run()
print(stats)
print(stats._strategy)

# Show initial performance plot
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    risk_per_trade=[0.01, 0.02],  # Test 1% and 2% risk per trade
    profit_target=[0.01, 0.02, 0.03],  # Test 1%, 2%, and 3% profit targets
    stop_loss=[0.005, 0.01, 0.015],  # Test 0.5%, 1%, and 1.5% stop losses
    maximize='Return [%]'
)
print(optimization_results)

# Show optimized results and final plot
bt.plot()