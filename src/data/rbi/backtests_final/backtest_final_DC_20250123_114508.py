import numpy as np
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import BernoulliRBM
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.base import BaseEstimator, ClassifierMixin
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Custom Deep Learning Model (RBM + FFNN)
class RBMModel(BaseEstimator, ClassifierMixin):
    def __init__(self, n_components=40, n_iter=20, learning_rate=0.01, random_state=42):
        self.n_components = n_components
        self.n_iter = n_iter
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.model = Pipeline([
            ('rbm', BernoulliRBM(n_components=n_components, n_iter=n_iter, learning_rate=learning_rate, random_state=random_state)),
            ('logistic', LogisticRegression(solver='lbfgs', max_iter=1000))
        ])

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def predict(self, X):
        return self.model.predict(X)

# Strategy Class
class EnhancedMomentumStrategy(Strategy):
    # Parameters
    n_months = 12  # Number of months for cumulative returns
    n_days = 20    # Number of days for cumulative returns
    top_decile = 0.1  # Top decile for long positions
    bottom_decile = 0.1  # Bottom decile for short positions
    risk_per_trade = 0.01  # Risk per trade (1% of capital)
    stop_loss = 0.05  # Stop loss (5%)
    take_profit = 0.10  # Take profit (10%)

    def init(self):
        # Preprocess data
        self.data['MonthlyReturns'] = self.data['Close'].pct_change(periods=self.n_months)
        self.data['DailyReturns'] = self.data['Close'].pct_change(periods=self.n_days)
        self.data['JanuaryIndicator'] = self.data.index.month == 1

        # Normalize returns using z-scores
        self.scaler = StandardScaler()
        self.data[['MonthlyReturns', 'DailyReturns']] = self.scaler.fit_transform(self.data[['MonthlyReturns', 'DailyReturns']])

        # Train the model
        X = self.data[['MonthlyReturns', 'DailyReturns', 'JanuaryIndicator']].dropna()
        y = (self.data['Close'].shift(-1) > self.data['Close']).astype(int).dropna()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = RBMModel(n_components=40, n_iter=20, learning_rate=0.01, random_state=42)
        self.model.fit(X_train, y_train)

        # Debug prints
        print("🌙 Model trained successfully! ✨")
        print(classification_report(y_test, self.model.predict(X_test)))

    def next(self):
        # Predict class 2 probabilities
        X = self.data[['MonthlyReturns', 'DailyReturns', 'JanuaryIndicator']].iloc[-1].values.reshape(1, -1)
        prob_class_2 = self.model.predict_proba(X)[0][1]

        # Rank stocks based on predicted probabilities
        self.data['PredictedClass2'] = prob_class_2
        self.data['Rank'] = self.data['PredictedClass2'].rank(pct=True)

        # Long positions (top decile)
        if self.data['Rank'].iloc[-1] >= 1 - self.top_decile:
            if not self.position:
                self.buy(size=self.calculate_position_size())
                print(f"🚀 Entering Long Position: {self.data.index[-1]} | Predicted Probability: {prob_class_2:.2f}")

        # Short positions (bottom decile)
        elif self.data['Rank'].iloc[-1] <= self.bottom_decile:
            if not self.position:
                self.sell(size=self.calculate_position_size())
                print(f"🌑 Entering Short Position: {self.data.index[-1]} | Predicted Probability: {prob_class_2:.2f}")

        # Exit positions after one month
        if self.position and (self.data.index[-1] - self.position.entry_time).days >= 30:
            self.position.close()
            print(f"🌕 Closing Position: {self.data.index[-1]}")

    def calculate_position_size(self):
        # Calculate position size based on risk percentage
        risk_amount = self.equity * self.risk_per_trade
        stop_loss_amount = self.data['Close'].iloc[-1] * self.stop_loss
        position_size = risk_amount / stop_loss_amount
        return position_size

# Data Preprocessing
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

    # Convert datetime column
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.set_index('datetime', inplace=True)

    return data

# Load data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)
data = preprocess_data(data)

# Run Backtest
bt = Backtest(data, EnhancedMomentumStrategy, cash=1_000_000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)

# Plot initial performance
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    n_months=range(6, 18, 2),
    n_days=range(10, 30, 2),
    top_decile=[0.05, 0.1, 0.15],
    bottom_decile=[0.05, 0.1, 0.15],
    risk_per_trade=[0.01, 0.02, 0.03],
    stop_loss=[0.03, 0.05, 0.07],
    take_profit=[0.08, 0.10, 0.12],
    maximize='Sharpe Ratio'
)

print("🌙 Optimization Results: ✨")
print(optimization_results)

# Plot optimized performance
bt.plot()