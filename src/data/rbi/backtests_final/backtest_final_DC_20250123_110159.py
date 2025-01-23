import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# Moon Dev themed debug prints 🌙 ✨ 🚀
def moon_dev_print(message):
    print(f"🌙 {message} ✨")

# Data preprocessing
def preprocess_data(data):
    # Clean column names
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
    
    # Calculate cumulative returns
    data['12_month_returns'] = data['Close'].pct_change(12)
    data['20_day_returns'] = data['Close'].pct_change(20)
    
    # Normalize returns using z-scores
    scaler = StandardScaler()
    data['12_month_returns_z'] = scaler.fit_transform(data[['12_month_returns']])
    data['20_day_returns_z'] = scaler.fit_transform(data[['20_day_returns']])
    
    # January indicator
    data['January'] = data.index.month == 1
    
    # Label stocks based on median returns
    data['Next_Month_Return'] = data['Close'].pct_change().shift(-1)
    data['Label'] = np.where(data['Next_Month_Return'] > data['Next_Month_Return'].median(), 2, 1)
    
    return data.dropna()

# Deep learning model
def build_model(input_shape):
    model = Sequential([
        Dense(64, input_shape=(input_shape,), activation='relu'),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Strategy class
class EnhancedMomentumStrategy(Strategy):
    def init(self):
        # Preprocess data
        self.data = preprocess_data(self.data.df)  # Access the DataFrame using .df
        
        # Split data into training and testing sets
        train_data = self.data[self.data.index.year < 1990]
        test_data = self.data[self.data.index.year >= 1990]
        
        # Features and labels
        X_train = train_data[['12_month_returns_z', '20_day_returns_z', 'January']]
        y_train = train_data['Label']
        X_test = test_data[['12_month_returns_z', '20_day_returns_z', 'January']]
        y_test = test_data['Label']
        
        # Train the model
        self.model = build_model(X_train.shape[1])
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        self.model.fit(X_train, y_train, validation_split=0.2, epochs=50, batch_size=32, callbacks=[early_stopping], verbose=0)
        
        # Predict probabilities for test data
        self.data['Predicted_Prob'] = self.model.predict(X_test)
        
        moon_dev_print("Model trained and predictions generated! 🚀")

    def next(self):
        # Rebalance portfolio at the start of each month
        if len(self.data) > 1 and self.data.index[-1].month != self.data.index[-2].month:
            # Rank stocks by predicted probability
            self.data['Rank'] = self.data['Predicted_Prob'].rank(pct=True)
            
            # Long top decile, short bottom decile
            long_stocks = self.data[self.data['Rank'] >= 0.9]
            short_stocks = self.data[self.data['Rank'] <= 0.1]
            
            # Close existing positions
            for trade in self.trades:
                self.position.close()
            
            # Open new positions
            for stock in long_stocks.index:
                self.buy(sl=0.95 * self.data.loc[stock, 'Close'], tp=1.05 * self.data.loc[stock, 'Close'])
            for stock in short_stocks.index:
                self.sell(sl=1.05 * self.data.loc[stock, 'Close'], tp=0.95 * self.data.loc[stock, 'Close'])
            
            moon_dev_print(f"Portfolio rebalanced! Long: {len(long_stocks)}, Short: {len(short_stocks)} 🌙")

# Load data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv', parse_dates=['datetime'], index_col='datetime')

# Run backtest
bt = Backtest(data, EnhancedMomentumStrategy, cash=1_000_000, commission=0.001)
stats = bt.run()
moon_dev_print("Initial backtest completed! 🌙")
print(stats)
print(stats._strategy)

# Plot initial performance
bt.plot()

# Optimize parameters (if applicable)
# Example: Optimize stop-loss and take-profit levels
optimized_stats = bt.optimize(
    sl=range(90, 96, 1),
    tp=range(104, 110, 1),
    maximize='Return [%]'
)
moon_dev_print("Optimization completed! 🚀")
print(optimized_stats)

# Plot optimized performance
bt.plot()