# Import necessary libraries
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

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
class VWAPMeanReversion(Strategy):
    # Parameters for optimization
    deviation_threshold = 1.0  # Percentage deviation from VWAP
    rsi_period = 14  # RSI period for overbought/oversold confirmation
    take_profit_pct = 0.5  # Take profit percentage
    stop_loss_pct = 1.0  # Stop loss percentage
    max_daily_loss_pct = 5.0  # Maximum daily loss percentage
    max_daily_trades = 5  # Maximum trades per day
    time_exit_minutes = 60  # Time-based exit in minutes

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        # Calculate RSI
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        # Track daily metrics
        self.daily_trades = 0
        self.daily_pnl = 0
        self._equity = self.equity  # Track initial equity for daily PnL calculation

    def next(self):
        # Check if daily loss limit is hit
        if self.daily_pnl <= -self.max_daily_loss_pct / 100 * self._equity:
            print(f"🌙 Moon Dev Alert: Daily loss limit hit! Stopping trading for the day. 🌙")
            return

        # Check if maximum daily trades are reached
        if self.daily_trades >= self.max_daily_trades:
            print(f"🌙 Moon Dev Alert: Maximum daily trades reached! Stopping trading for the day. 🌙")
            return

        # Calculate deviation from VWAP
        price = self.data.Close[-1]
        vwap_value = self.vwap[-1]
        deviation = abs((price - vwap_value) / vwap_value) * 100

        # Long entry logic
        if price < vwap_value and deviation >= self.deviation_threshold and self.rsi[-1] < 30:
            if not self.position:
                print(f"🌙 Moon Dev Signal: Long entry triggered! Price: {price}, VWAP: {vwap_value}, RSI: {self.rsi[-1]} 🌙")
                self.buy()
                self.daily_trades += 1
                # Set take profit and stop loss
                take_profit = price * (1 + self.take_profit_pct / 100)
                stop_loss = price * (1 - self.stop_loss_pct / 100)
                self.position.take_profit = take_profit
                self.position.stop_loss = stop_loss

        # Short entry logic
        elif price > vwap_value and deviation >= self.deviation_threshold and self.rsi[-1] > 70:
            if not self.position:
                print(f"🌙 Moon Dev Signal: Short entry triggered! Price: {price}, VWAP: {vwap_value}, RSI: {self.rsi[-1]} 🌙")
                self.sell()
                self.daily_trades += 1
                # Set take profit and stop loss
                take_profit = price * (1 - self.take_profit_pct / 100)
                stop_loss = price * (1 + self.stop_loss_pct / 100)
                self.position.take_profit = take_profit
                self.position.stop_loss = stop_loss

        # Time-based exit logic
        if self.position and len(self.data) - self.position.entry_bar >= self.time_exit_minutes / 15:
            print(f"🌙 Moon Dev Signal: Time-based exit triggered! Closing position. 🌙")
            self.position.close()

        # Update daily PnL
        if self.position:
            self.daily_pnl = (self.equity - self._equity) / self._equity * 100

# Run initial backtest
bt = Backtest(data, VWAPMeanReversion, cash=1_000_000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    deviation_threshold=range(5, 20, 5),  # Test deviation thresholds from 0.5% to 2%
    rsi_period=range(10, 20, 2),  # Test RSI periods from 10 to 20
    take_profit_pct=range(5, 20, 5),  # Test take profit percentages from 0.5% to 2%
    stop_loss_pct=range(10, 20, 5),  # Test stop loss percentages from 1% to 2%
    max_daily_loss_pct=range(3, 6, 1),  # Test maximum daily loss percentages from 3% to 5%
    max_daily_trades=range(3, 6, 1),  # Test maximum daily trades from 3 to 5
    time_exit_minutes=range(30, 90, 15),  # Test time-based exit windows from 30 to 90 minutes
    maximize='Sharpe Ratio'  # Optimize for Sharpe Ratio
)
print(optimization_results)
bt.plot()