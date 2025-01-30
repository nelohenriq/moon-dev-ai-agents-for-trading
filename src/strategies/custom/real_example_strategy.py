from src.strategies.base_strategy import BaseStrategy
from pycoingecko import CoinGeckoAPI
import pandas as pd
import time
import os

class RealExampleStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Real Example Strategy 🚀")
        self.rsi_period = 14
        self.short_ma_period = 50
        self.long_ma_period = 200
        self.symbol = "bitcoin"  # CoinGecko uses "bitcoin" instead of "BTC-USD"
        self.cg = CoinGeckoAPI(demo_api_key=os.environ.get("COINGECKO_API_KEY"))
    
    def get_historical_data(self, symbol: str, vs_currency: str = 'usd', days: int = 500) -> pd.DataFrame:
        """
        Fetch historical price data from CoinGecko API.
        """
        # Get historical data from the last 'days' days
        data = self.cg.get_coin_market_chart_range_by_id(id=symbol, vs_currency=vs_currency, 
                                                         from_timestamp=int(time.time()) - (days * 365), 
                                                         to_timestamp=int(time.time()))
        
        # Extract the 'prices' data (timestamp and price)
        prices = data['prices']
        
        # Convert to DataFrame
        df = pd.DataFrame(prices, columns=['time', 'close'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')  # Convert timestamp to datetime
        df.set_index('time', inplace=True)
        return df
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate the RSI for the given DataFrame of price data.
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the short and long period moving averages.
        """
        df['short_ma'] = df['close'].rolling(window=self.short_ma_period).mean()
        df['long_ma'] = df['close'].rolling(window=self.long_ma_period).mean()
        return df
    
    def generate_signals(self) -> dict:
        """
        Generate a trading signal based on moving average crossover and RSI.
        """
        # Fetch historical data from CoinGecko
        df = self.get_historical_data(self.symbol)
        
        # Calculate RSI and moving averages
        df['rsi'] = self.calculate_rsi(df)
        df = self.calculate_moving_averages(df)
        
        # Signal generation logic:
        # 1. If short MA crosses above long MA and RSI < 30, it’s a BUY signal (bullish)
        # 2. If short MA crosses below long MA and RSI > 70, it’s a SELL signal (bearish)
        signal = None
        direction = "NEUTRAL"
        reason = "No signal generated."
        
        if df['short_ma'].iloc[-1] > df['long_ma'].iloc[-1] and df['rsi'].iloc[-1] < 30:
            signal = 1  # Buy signal strength
            direction = "BUY"
            reason = "🚀 Moving averages indicate a bullish trend, and RSI is oversold."
        
        elif df['short_ma'].iloc[-1] < df['long_ma'].iloc[-1] and df['rsi'].iloc[-1] > 70:
            signal = 0  # Sell signal strength
            direction = "SELL"
            reason = "📉 Moving averages indicate a bearish trend, and RSI is overbought."
        
        # Return signal and metadata
        return {
            'token': self.symbol,
            'signal': signal,
            'direction': direction,
            'metadata': {
                'reason': reason,
                'indicators': {
                    'rsi': df['rsi'].iloc[-1],
                    'short_ma': df['short_ma'].iloc[-1],
                    'long_ma': df['long_ma'].iloc[-1]
                }
            }
        }
