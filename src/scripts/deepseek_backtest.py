import pandas as pd
import yfinance as yf
from backtesting import Backtest, Strategy
import numpy as np

class VWAPVolumeStrategy(Strategy):
    # Define the parameters for the strategy
    vwap_window = 20  # VWAP calculation window
    volume_threshold = 1.5  # Volume threshold multiplier (e.g., 1.5x average volume)

    def init(self):
        # Calculate VWAP using numpy operations
        typical_price = (self.data.High + self.data.Low + self.data.Close) / 3
        volume = self.data.Volume
        
        # Create rolling sum arrays
        rolling_sum_price_volume = np.convolve(typical_price * volume, np.ones(self.vwap_window), 'valid')
        rolling_sum_volume = np.convolve(volume, np.ones(self.vwap_window), 'valid')
        
        # Pad the arrays to match original length
        pad_length = len(typical_price) - len(rolling_sum_price_volume)
        self.vwap = np.pad(rolling_sum_price_volume / rolling_sum_volume, (pad_length, 0), 'constant', constant_values=np.nan)
        
        # Calculate average volume
        self.avg_volume = np.convolve(volume, np.ones(self.vwap_window), 'valid') / self.vwap_window
        self.avg_volume = np.pad(self.avg_volume, (pad_length, 0), 'constant', constant_values=np.nan)
        
        print("🌙 MOON DEV: VWAP and Volume calculations initialized successfully! 🚀")

    def next(self):
        # Go long if the closing price is above VWAP and volume is above the threshold
        if self.data.Close[-1] > self.vwap[-1] and self.data.Volume[-1] > self.volume_threshold * self.avg_volume[-1]:
            if not self.position.is_long:
                self.buy()  # Enter long position
                print("🌕 MOON DEV: Long position entered! 🚀📈")

        # Go short if the closing price is below VWAP and volume is above the threshold
        elif self.data.Close[-1] < self.vwap[-1] and self.data.Volume[-1] > self.volume_threshold * self.avg_volume[-1]:
            if not self.position.is_short:
                self.sell()  # Enter short position
                print("🌑 MOON DEV: Short position entered! 🚀📉")

# Download Apple (AAPL) data from Yahoo Finance
ticker = "AMZN"
try:
    data = yf.download(ticker, start="2020-01-01", end="2023-01-01")
    
    # Print the structure of the DataFrame
    print(data.head())  # Print the first few rows of the DataFrame
    print(data.columns)  # Print the column names
    
    # Flatten the MultiIndex
    data.columns = data.columns.droplevel(1)  # Drop the second level of the MultiIndex
    
    # Reset index if necessary
    data.reset_index(inplace=True)

    # Drop rows with missing data
    data = data.dropna()

    # Run the backtest
    bt = Backtest(data, VWAPVolumeStrategy, cash=10000, commission=.002)
    stats = bt.run()

    # Print the results
    print(stats)

    # Plot the backtest results
    bt.plot()

except Exception as e:
    print(f"❌ Error downloading data or running backtest: {str(e)}")