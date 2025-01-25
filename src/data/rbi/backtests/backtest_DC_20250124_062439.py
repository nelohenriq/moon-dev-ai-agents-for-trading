Below is the implementation of the backtest for the momentum trading strategy enhanced by deep learning. The implementation includes all the necessary components, such as data handling, strategy logic, risk management, and parameter optimization. The strategy uses TA-Lib for indicator calculations and follows the rules provided.

---

### Backtest Implementation

```python
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
import os

# Constants
DATA_DIR = "data"
MODEL_PATH = "deep_learning_model.h5"  # Path to the pre-trained deep learning model
INITIAL_CAPITAL = 1_000_000
RISK_PER_TRADE = 0.02  # 2% of total capital per trade
TAKE_PROFIT = 0.02  # 2% profit target
STOP_LOSS = 0.01  # 1% stop loss
HOLDING_PERIOD = 5  # Maximum holding period in days

# Data Handling
def load_and_prepare_data(filepath):
    data = pd.read_csv(filepath)
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
    data.set_index('datetime', inplace=True)
    return data

# Deep Learning Model Prediction
def predict_price_direction(model, data):
    # Prepare input data for the model
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data[['Open', 'High', 'Low', 'Close', 'Volume']])
    # Reshape for LSTM input (samples, timesteps, features)
    scaled_data = scaled_data.reshape((1, scaled_data.shape[0], scaled_data.shape[1]))
    # Predict price direction
    prediction = model.predict(scaled_data)
    return prediction[0][0]  # Probability of positive price movement

# Strategy Class
class MomentumDeepLearningStrategy(Strategy):
    # Parameters for optimization
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    holding_period = HOLDING_PERIOD

    def init(self):
        # Calculate indicators
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.macd, self.macd_signal_line, _ = self.I(talib.MACD, self.data.Close, 
                                                     fastperiod=self.macd_fast, 
                                                     slowperiod=self.macd_slow, 
                                                     signalperiod=self.macd_signal)
        # Load the deep learning model
        self.model = load_model(MODEL_PATH)
        # Track holding period
        self.holding_days = 0

    def next(self):
        # Predict price direction using the deep learning model
        lookback_data = self.data.df.iloc[-60:]  # Use last 60 periods for prediction
        prediction = predict_price_direction(self.model, lookback_data)
        
        # Entry Logic
        if not self.position:
            # Buy Signal: Model predicts positive movement and momentum indicators confirm
            if prediction > 0.5 and self.rsi[-1] > 50 and crossover(self.macd, self.macd_signal_line):
                # Calculate position size based on risk management
                risk_amount = INITIAL_CAPITAL * RISK_PER_TRADE
                stop_loss_price = self.data.Close[-1] * (1 - STOP_LOSS)
                position_size = risk_amount / (self.data.Close[-1] - stop_loss_price)
                # Enter the trade
                self.buy(size=position_size)
                self.holding_days = 0
                print(f"🌙 Moon Dev Buy Signal! Entering trade at {self.data.Close[-1]} 🚀")

        # Exit Logic
        if self.position:
            self.holding_days += 1
            # Take Profit
            if self.data.Close[-1] >= self.position.entry_price * (1 + TAKE_PROFIT):
                self.position.close()
                print(f"✨ Moon Dev Take Profit! Exiting trade at {self.data.Close[-1]} 🎉")
            # Stop Loss
            elif self.data.Close[-1] <= self.position.entry_price * (1 - STOP_LOSS):
                self.position.close()
                print(f"🌧 Moon Dev Stop Loss! Exiting trade at {self.data.Close[-1]} 🛑")
            # Time-Based Exit
            elif self.holding_days >= self.holding_period:
                self.position.close()
                print(f"⏳ Moon Dev Time Exit! Exiting trade after {self.holding_days} days 🕒")

# Load Data
data = load_and_prepare_data(f"{DATA_DIR}/BTC-USD-15m.csv")

# Run Backtest
bt = Backtest(data, MomentumDeepLearningStrategy, cash=INITIAL_CAPITAL, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)

# Initial Performance Plot
bt.plot()

# Parameter Optimization
optimization_results = bt.optimize(
    rsi_period=range(10, 20, 2),
    macd_fast=range(10, 20, 2),
    macd_slow=range(20, 30, 2),
    macd_signal=range(7, 12, 1),
    maximize='Sharpe Ratio'
)
print(optimization_results)

# Optimized Performance Plot
bt.plot()
```

---

### Explanation of Key Components

1. **Data Handling**:
   - The `load_and_prepare_data` function cleans and prepares the data for backtesting.
   - Ensures proper column mapping and removes unnecessary columns.

2. **Deep Learning Model**:
   - The `predict_price_direction` function uses a pre-trained deep learning model to predict price direction.
   - The model is loaded using TensorFlow/Keras.

3. **Strategy Logic**:
   - The `MomentumDeepLearningStrategy` class implements the strategy logic.
   - Uses RSI and MACD indicators for momentum confirmation.
   - Combines deep learning predictions with technical indicators for entry/exit signals.

4. **Risk Management**:
   - Position sizing is calculated based on a fixed percentage of total capital.
   - Includes stop loss, take profit, and time-based exit rules.

5. **Parameter Optimization**:
   - The `optimize` method is used to find the best parameters for RSI, MACD, and other indicators.
   - Optimizes for the Sharpe Ratio.

6. **Moon Dev Themed Debug Prints**:
   - Fun and informative debug messages are printed for entry/exit signals.

---

### Execution Order

1. **Initial Backtest**:
   - Run the backtest with default parameters.
   - Print full stats and plot the initial performance.

2. **Optimization**:
   - Optimize the strategy parameters.
   - Print the optimized results and plot the final performance.

---

Let me know if you need further assistance! 🌙✨🚀