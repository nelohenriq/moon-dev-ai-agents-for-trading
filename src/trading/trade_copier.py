from src import nice_funcs as n
from src.config import EXCLUDED_TOKENS

class TradeCopier:
    def __init__(self, max_slippage: float = 1.0):
        self.max_slippage = max_slippage
        
    async def copy_trade(self, trade_data: dict):
        if trade_data['token'] in EXCLUDED_TOKENS:
            return False
            
        if trade_data['action'] == 'BUY':
            return await self._execute_buy(
                token=trade_data['token'],
                amount_usd=trade_data['usd_value'] * 0.95  # 95% of whale's position
            )
        else:
            return await self._execute_sell(
                token=trade_data['token']
            )
