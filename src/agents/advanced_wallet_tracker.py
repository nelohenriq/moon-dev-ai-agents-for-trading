from src.agents.base_agent import BaseAgent
from src import nice_funcs as n
import pandas as pd
from datetime import datetime
from termcolor import cprint
from telegram import Bot
import plotly.graph_objects as go
import os
import time

class AdvancedWalletTracker(BaseAgent):
    def __init__(self, target_wallets: list, min_usd_value: float = 100):
        super().__init__("advanced_wallet_tracker")
        self.target_wallets = target_wallets
        self.last_holdings = {}
        self.performance_metrics = {}
        self.min_usd_value = min_usd_value
        self.wallet_metrics = {}  # Track metrics for each wallet
        self.last_known_balances = {}  # Track previous token balances
        self.token_prices = {}  # Cache token prices
        self.notification_history = {}  # Track sent notifications
        
        # Initialize notification clients
        self.telegram_bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        
    async def track_and_notify(self):
        for wallet in self.target_wallets:
            changes = await self._analyze_wallet(wallet)
            if changes:
                await self._send_notifications(wallet, changes)
                await self._update_dashboard(wallet)
                await self._execute_copy_trades(changes)
                
    async def _analyze_wallet(self, wallet):
        current_holdings = n.fetch_wallet_holdings_og(wallet)
        significant_changes = self._filter_significant_changes(
            self.last_holdings.get(wallet, pd.DataFrame()), 
            current_holdings
        )
        self._update_metrics(wallet, current_holdings)
        return significant_changes

    def _filter_significant_changes(self, changes, token_prices):
        """Filter for significant token balance changes"""
        significant_changes = []
        
        
        for change in changes:
            # Get token price from provided prices dict
            token_price = token_prices.get(change['token'], 0)
            usd_value = change['amount'] * token_price
            
            # Keep changes above minimum USD threshold
            if abs(usd_value) >= self.min_usd_value:
                change['usd_value'] = usd_value
                significant_changes.append(change)
                
        return significant_changes

    def _update_metrics(self, wallet_address, changes):
        """Update tracking metrics for a wallet"""
        if wallet_address not in self.wallet_metrics:
            self.wallet_metrics[wallet_address] = {
                'total_volume': 0,
                'trade_count': 0,
                'last_trade_time': None,
                'tokens_traded': set()
            }
        
        metrics = self.wallet_metrics[wallet_address]
        
        for change in changes:
            metrics['total_volume'] += abs(change['usd_value'])
            metrics['trade_count'] += 1
            metrics['last_trade_time'] = time.time()
            metrics['tokens_traded'].add(change['token'])

    def _update_dashboard(self, wallet):
        fig = go.Figure()
        # Add performance charts
        for token, metrics in self.performance_metrics[wallet].items():
            fig.add_trace(go.Line(x=metrics['timestamps'], y=metrics['values']))
        fig.write_html(f"dashboard_{wallet}.html")
