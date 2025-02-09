import time
import requests
from solana.rpc.api import Client

# Configuration
TOKEN_ADDRESS = "YOUR_SOLANA_TOKEN_ADDRESS"
PUMPFUN_API = "https://api.pump.fun/tokens"  # Hypothetical API
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"
SOLSCAN_API = "https://public-api.solscan.io/token"  # Solana blockchain data
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

# Connect to Solana node
solana_client = Client("https://api.mainnet-beta.solana.com")

# Fetch initial data
def fetch_initial_data():
    # Fetch price and liquidity from DexScreener
    dex_data = requests.get(f"{DEXSCREENER_API}/{TOKEN_ADDRESS}").json()
    price = float(dex_data["pairs"][0]["priceUsd"])
    liquidity = float(dex_data["pairs"][0]["liquidity"]["usd"])

    # Fetch token metadata from Solscan
    solscan_data = requests.get(f"{SOLSCAN_API}/{TOKEN_ADDRESS}").json()
    total_supply = float(solscan_data["supply"])
    creator = solscan_data["info"]["mintAuthority"]

    return {
        "price": price,
        "liquidity": liquidity,
        "total_supply": total_supply,
        "creator": creator,
    }

# Send Telegram alert
def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.get(url, params=params)

# Monitor price changes
def monitor_price(initial_price):
    while True:
        dex_data = requests.get(f"{DEXSCREENER_API}/{TOKEN_ADDRESS}").json()
        current_price = float(dex_data["pairs"][0]["priceUsd"])
        price_change = abs((current_price - initial_price) / initial_price) * 100

        if price_change > 10:  # 10% threshold
            send_alert(f"🚨 Price Alert: {price_change:.2f}% change! Current price: ${current_price}")

        time.sleep(300)  # Check every 5 minutes

# Monitor liquidity changes
def monitor_liquidity(initial_liquidity):
    while True:
        dex_data = requests.get(f"{DEXSCREENER_API}/{TOKEN_ADDRESS}").json()
        current_liquidity = float(dex_data["pairs"][0]["liquidity"]["usd"])
        liquidity_change = abs((current_liquidity - initial_liquidity) / initial_liquidity) * 100

        if liquidity_change > 5:  # 5% threshold
            send_alert(f"🚨 Liquidity Alert: {liquidity_change:.2f}% change! Current liquidity: ${current_liquidity}")

        time.sleep(600)  # Check every 10 minutes

# Monitor whale activity
def monitor_whales(total_supply):
    while True:
        # Fetch top holders from Solscan
        holders_url = f"{SOLSCAN_API}/{TOKEN_ADDRESS}/holders"
        holders_data = requests.get(holders_url).json()

        for holder in holders_data["data"]:
            balance = float(holder["amount"])
            if balance > 0.05 * total_supply:  # >5% of supply
                send_alert(f"🐋 Whale Alert: {holder['address']} holds {balance / total_supply * 100:.2f}% of supply!")

        time.sleep(1800)  # Check every 30 minutes

# Monitor suspicious transactions
def monitor_transactions(total_supply):
    while True:
        # Fetch recent transactions from Solscan
        txs_url = f"{SOLSCAN_API}/{TOKEN_ADDRESS}/transactions"
        txs_data = requests.get(txs_url).json()

        for tx in txs_data["data"]:
            if float(tx["amount"]) > 0.05 * total_supply:  # >5% of supply
                send_alert(f"🚨 Suspicious Transaction: {tx['amount']} $TOKEN sent to {tx['to']}!")

        time.sleep(60)  # Check every minute

# Main function
def main():
    initial_data = fetch_initial_data()

    # Start monitoring threads
    import threading
    threading.Thread(target=monitor_price, args=(initial_data["price"],)).start()
    threading.Thread(target=monitor_liquidity, args=(initial_data["liquidity"],)).start()
    threading.Thread(target=monitor_whales, args=(initial_data["total_supply"],)).start()
    threading.Thread(target=monitor_transactions).start()

if __name__ == "__main__":
    main()
