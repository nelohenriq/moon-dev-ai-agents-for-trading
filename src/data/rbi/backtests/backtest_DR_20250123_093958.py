Here's the backtesting implementation for your Swing Trading Strategy:

```python
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder
from backtesting.test import SMA, EMA

class SwingStrategy(Strategy):
    # Strategy parameters
    n1 = 8    # EMA period
    n2 = 200  # SMA period
    consol_period = 20  # Consolidation lookback
    volume_threshold = 1.2  # 20% above average volume
    
    def init(self):
        # Calculate indicators
        self.ema8 = self.I(EMA, self.data.Close, self.n1)
        self.sma200 = self.I(SMA, self.data.Close, self.n2)
        self.vol_avg = self.I(SMA, self.data.Volume, 30)
        
        # Track resistance levels and pullbacks
        self.consol_high = self.I(lambda x: x.rolling(self.consol_period).max(), self.data.High)
        self.consol_low = self.I(lambda x: x.rolling(self.consol_period).min(), self.data.Low)
        self.in_consolidation = self.data.High < self.consol_high * 1.03  # 3% range
        
    def next(self):
        price = self.data.Close[-1]
        volume = self.data.Volume[-1]
        
        # Risk management - max 2% risk per trade
        if not self.position:
            risk_per_trade = self.equity * 0.02
            atr = self.data.Close[-20:].std()  # Simple volatility measure
            position_size = risk_per_trade / (atr * 2)  # 2% risk with 2x ATR stop
            position_size = min(position_size, self.equity * 0.5)  # Max 50% equity per trade
        
        # Entry conditions
        if (price > self.sma200[-1] and
            self.in_consolidation[-self.consol_period:-1].all() and
            price > self.consol_high[-1] and
            volume > self.vol_avg[-1] * self.volume_threshold):
            
            # Wait for pullback to 8 EMA
            if price <= self.ema8[-1] * 1.02:  # Within 2% of EMA
                self.buy(size=position_size, 
                        sl=price * 0.97,  # 3% initial stop
                        tag='main_entry')
                
        # Exit conditions
        for trade in self.trades:
            if trade.is_long:
                current_pct = (price / trade.entry_price - 1) * 100
                
                # Partial profits
                if not trade.tag.endswith('_partial'):
                    if current_pct >= 5:  # First resistance (simplified)
                        self.sell(size=trade.size*0.25, 
                                 tag='25%_partial')
                        trade.sl = trade.entry_price  # Move to breakeven
                        
                    elif current_pct >= 10:  # 10% above entry
                        self.sell(size=trade.size*0.25,
                                 tag='25%_partial')
                        
                # Trail remaining 50% with EMA
                if trade.size > 0:
                    trail_stop = self.ema8[-1] * 0.99  # 1% below EMA
                    trade.sl = max(trade.sl or 0, trail_stop)
                
                # Full exit conditions
                if crossover(self.ema8, self.data.Close):
                    self.sell(size=trade.size, tag='ema_cross_exit')

# Load and prepare data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv',
                   parse_dates=['time'], index_col='time')
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}).dropna()

# Run backtest
bt = Backtest(data, SwingStrategy, cash=100000, commission=.002)
stats = bt.run()

# Optimize parameters (example)
# opt_stats = bt.optimize(
#     n1=range(5, 15),
#     consol_period=range(10, 30, 5),
#     volume_threshold=[1.1, 1.2, 1.3],
#     maximize='Equity Final [$]',
#     max_tries=50)

print(stats)
bt.plot()
```

Key features of this implementation:

1. **Indicators**:
   - 8-period EMA for momentum tracking
   - 200-period SMA for trend filtering
   - 30-period volume average for breakout confirmation

2. **Entry Logic**:
   - Price must be above 200 SMA
   - Consolidation detection using 3% price range
   - Breakout confirmation with volume surge
   - Pullback entry to 8 EMA

3. **Exit Logic**:
   - 25% position sold at 5% profit (simplified resistance)
   - Another 25% at 10% profit
   - 50% trailed with EMA stop
   - Full exit on EMA crossunder

4. **Risk Management**:
   - 2% risk per trade based on volatility (ATR)
   - Position sizing based on stop distance
   - Max 50% equity per trade

5. **Optimization**:
   - Example optimization included (commented out)
   - Parameters: EMA period, consolidation length, volume threshold

To use this:
1. Install required packages: `pip install backtesting pandas numpy`
2. Adjust data path if needed
3. Modify parameters in optimization section
4. Review equity curve and statistics output

The strategy includes simplifications for automated backtesting where manual pattern recognition would normally be used (like resistance levels). You may want to:
1. Add additional filters for market cap/volume (currently simulated)
2. Adjust profit targets based on your risk profile
3. Fine-tune consolidation detection parameters
4. Add additional safeguards for volatile markets