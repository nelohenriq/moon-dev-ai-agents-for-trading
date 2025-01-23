import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import BernoulliRBM
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPClassifier

# Moon Dev themed debug prints 🌙 ✨ 🚀
def moon_dev_print(message):
    print(f"🌙 {message} ✨")

# Custom transformer for cumulative returns and z-score normalization
class CumulativeReturnsTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, lookback_period):
        self.lookback_period = lookback_period

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        cumulative_returns = X.rolling(window=self.lookback_period).sum()
        z_scores = (cumulative_returns - cumulative_returns.mean()) / cumulative_returns.std()
        return z_scores.fillna(0)

# Strategy class
class EnhancedMomentumStrategy(Strategy):
    # Strategy parameters
    monthly_lookback = 12
    daily_lookback = 20
    top_decile = 0.1
    bottom_decile = 0.1
    min_price = 5

    def init(self):
        # Preprocess data
        self.data['MonthlyReturns'] = self.I(talib.ROC, self.data.Close, timeperiod=21)  # Approximate monthly returns
        self.data['DailyReturns'] = self.I(talib.ROC, self.data.Close, timeperiod=1)    # Daily returns

        # Cumulative returns and z-score normalization
        self.monthly_cumulative = CumulativeReturnsTransformer(self.monthly_lookback).transform(self.data['MonthlyReturns'])
        self.daily_cumulative = CumulativeReturnsTransformer(self.daily_lookback).transform(self.data['DailyReturns'])

        # January indicator
        self.data['JanuaryIndicator'] = self.data.index.month == 1

        # Combine features
        self.features = pd.concat([self.monthly_cumulative, self.daily_cumulative, self.data['JanuaryIndicator']], axis=1)
        self.features.columns = ['MonthlyCumulative', 'DailyCumulative', 'JanuaryIndicator']

        # Train model
        self.train_model()

    def train_model(self):
        # Prepare training data
        X = self.features.dropna()
        y = np.where(self.data['MonthlyReturns'].shift(-1) > self.data['MonthlyReturns'].shift(-1).median(), 1, 0)
        y = y[~X.index.duplicated(keep='first')]  # Align labels with features

        # Split into training and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Define model pipeline
        rbm = BernoulliRBM(n_components=40, learning_rate=0.01, n_iter=20, random_state=42, verbose=True)
        pca = PCA(n_components=4)
        mlp = MLPClassifier(hidden_layer_sizes=(50,), max_iter=100, random_state=42)
        self.model = Pipeline([('rbm', rbm), ('pca', pca), ('mlp', mlp)])

        # Train model
        moon_dev_print("Training model... 🚀")
        self.model.fit(X_train, y_train)

        # Evaluate model
        y_pred = self.model.predict(X_test)
        moon_dev_print("Model evaluation results:")
        print(classification_report(y_test, y_pred))

    def next(self):
        # Predict probabilities
        if len(self.data) < self.monthly_lookback + self.daily_lookback:
            return  # Skip if not enough data

        current_features = self.features.iloc[-1].values.reshape(1, -1)
        prob_class_2 = self.model.predict_proba(current_features)[0][1]

        # Portfolio formation
        if self.data.Close[-1] < self.min_price:
            return  # Exclude stocks below minimum price

        # Long positions (top decile)
        if prob_class_2 >= np.percentile(self.model.predict_proba(self.features)[:, 1], 90):
            moon_dev_print("Opening long position 🌙")
            self.buy(size=1)

        # Short positions (bottom decile)
        elif prob_class_2 <= np.percentile(self.model.predict_proba(self.features)[:, 1], 10):
            moon_dev_print("Opening short position 🌙")
            self.sell(size=1)

        # Close positions at the end of the month
        if self.data.index[-1].month != self.data.index[-2].month:
            moon_dev_print("Closing all positions for rebalancing 🌙")
            self.position.close()

# Load data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")
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

# Convert datetime
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# Run backtest
moon_dev_print("Starting backtest... 🚀")
bt = Backtest(data, EnhancedMomentumStrategy, cash=1_000_000, commission=0.002)
stats = bt.run()
moon_dev_print("Backtest complete! 🌙")
print(stats)
print(stats._strategy)

# Plot results
bt.plot()

# Optimize parameters
moon_dev_print("Optimizing parameters... 🚀")
optimized_stats = bt.optimize(
    monthly_lookback=range(10, 15),
    daily_lookback=range(18, 22),
    top_decile=[0.1, 0.15],
    bottom_decile=[0.1, 0.15],
    min_price=[5, 10],
    maximize='Return [%]'
)
moon_dev_print("Optimization complete! 🌙")
print(optimized_stats)

# Plot optimized results
bt.plot()