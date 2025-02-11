from telegram import Bot
import os

class NotificationSystem:
    def __init__(self):
        self.telegram_bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        
    async def send_alert(self, message: str, trade_data: dict):
        # Format beautiful message with emojis
        formatted_msg = f"""
        🚨 New Whale Movement Detected! 🐋
        
        Wallet: {trade_data['wallet'][:8]}...
        Token: {trade_data['token']}
        Action: {trade_data['action']}
        Amount: ${trade_data['usd_value']:,.2f}
        
        🎯 Trade Copying Status: {trade_data['copy_status']}
        """
        
        await self._send_to_all_platforms(formatted_msg)
