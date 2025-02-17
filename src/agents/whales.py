import time
import requests
import os
import logging
import json
import threading
import base58
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configuration
TOKEN_ADDRESS = "4MpXgiYj9nEvN1xZYZ4qgB6zq5r2JMRy54WaQu5fpump"
DEXSCREENER_API = os.getenv("DEXSCREENER_API")
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


class MonitoringThreads:
    def __init__(self):
        self.threads = []
        self.running = True

    def add_thread(self, target, args=()):
        thread = threading.Thread(target=self._wrapped_target, args=(target, args))
        self.threads.append(thread)
        thread.start()

    def _wrapped_target(self, target, args):
        while self.running:
            try:
                target(*args)
            except Exception as e:
                logging.error(f"Error in {target.__name__}: {e}")
                time.sleep(60)

    def shutdown(self):
        self.running = False
        for thread in self.threads:
            thread.join()


class MonitorConfig:
    def __init__(self):
        self.config = {
            "price_change_threshold": 10,
            "liquidity_change_threshold": 5,
            "whale_threshold": 0.05,
            "market_cap_change_threshold": 7,
            "check_intervals": {
                "price": 300,
                "liquidity": 600,
                "whales": 1800,
                "transactions": 60,
                "market_cap": 300,
            },
        }

    def update_config(self, new_config):
        self.config.update(new_config)


class HealthCheck:
    def __init__(self):
        self.last_updates = {}

    def update(self, monitor_name):
        self.last_updates[monitor_name] = datetime.now()

    def check_health(self, max_delay_minutes=10):
        now = datetime.now()
        unhealthy = []
        for monitor, last_update in self.last_updates.items():
            if (now - last_update).total_seconds() > max_delay_minutes * 60:
                unhealthy.append(monitor)
        return unhealthy


def format_number(number, decimals=2):
    """Format numbers for readability in alerts"""
    if number >= 1_000_000:
        return f"${number/1_000_000:.{decimals}f}M"
    elif number >= 1_000:
        return f"${number/1_000:.{decimals}f}K"
    return f"${number:.{decimals}f}"


def make_api_request(url, payload, max_retries=3, initial_delay=1):
    """Make API requests with exponential backoff"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            delay = initial_delay * (2**attempt)
            time.sleep(delay)


def setup_logging():
    """Configure logging system"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("whale_monitor.log"), logging.StreamHandler()],
    )


def cleanup_wallet_history(wallet_history, max_age_hours=24):
    """Remove old wallet history entries"""
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    return {
        wallet: data
        for wallet, data in wallet_history.items()
        if data["last_seen"] > cutoff_time
    }


def save_monitoring_state(data, filename="monitor_state.json"):
    """Save monitoring state to file"""
    with open(filename, "w") as f:
        json.dump(data, f)


def load_monitoring_state(filename="monitor_state.json"):
    """Load monitoring state from file"""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def validate_solana_address(address):
    """Validate Solana address format"""
    try:
        decoded = base58.b58decode(address)
        return len(decoded) == 32
    except:
        return False


# Fetch initial data
def fetch_initial_data():
    # Fetch price and liquidity from DexScreener
    dex_data = requests.get(f"{DEXSCREENER_API}/{TOKEN_ADDRESS}").json()
    price = float(dex_data["pairs"][0]["priceUsd"])
    liquidity = float(dex_data["pairs"][0]["liquidity"]["usd"])

    # Get token metadata using Helius RPC
    helius_payload = {
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "getTokenSupply",
        "params": [TOKEN_ADDRESS],
    }

    supply_response = requests.post(
        RPC_ENDPOINT,
        headers={"Content-Type": "application/json"},
        json=helius_payload,
    ).json()

    total_supply = float(supply_response["result"]["value"]["amount"])

    creator_tokens = None
    creator = get_token_creator(TOKEN_ADDRESS)
    if creator:
        creator_tokens = get_creator_tokens(creator)

    market_cap = price * total_supply

    return {
        "price": price,
        "liquidity": liquidity,
        "total_supply": total_supply,
        "market_cap": market_cap,
        "creator": creator,
        "creator_tokens": creator_tokens,
    }


def check_lp_burn(lp_address):
    """Check if LP tokens are burned"""
    burn_addresses = [
        "1111111111111111111111111111111111111111",
        "deadbeef111111111111111111111111111111111",
    ]

    holders_payload = {
        "jsonrpc": "2.0",
        "id": "lp-holders",
        "method": "getProgramAccounts",
        "params": [
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            {
                "filters": [
                    {"dataSize": 165},
                    {"memcmp": {"offset": 0, "bytes": lp_address}},
                ],
                "encoding": "jsonParsed",
            },
        ],
    }

    holders = requests.post(
        RPC_ENDPOINT,
        headers={"Content-Type": "application/json"},
        json=holders_payload,
    ).json()

    return any(
        h["account"]["data"]["parsed"]["info"]["owner"] in burn_addresses
        for h in holders["result"]
    )


def get_token_creator(token_address):
    """Get token creator using Helius getAsset"""
    payload = {
        "jsonrpc": "2.0",
        "id": "token-info",
        "method": "getAsset",
        "params": {"id": token_address},
    }

    response = requests.post(
        RPC_ENDPOINT, headers={"Content-Type": "application/json"}, json=payload
    ).json()

    if "result" in response:
        authorities = response["result"].get("authorities", [])
        if authorities:
            return authorities[0].get("address")  # Return first authority address

    return None


def get_creator_tokens(creator_address):
    """Get all tokens created by address that are listed on Raydium with extended metrics"""

    search_payload = {
        "jsonrpc": "2.0",
        "id": "creator-tokens",
        "method": "searchAssets",
        "params": {
            "authorityAddress": creator_address,
            "tokenType": "fungible",
            "page": 1,
            "limit": 100,
            "options": {"showNativeBalance": True, "showCollectionMetadata": True},
        },
    }

    tokens_response = requests.post(
        RPC_ENDPOINT, headers={"Content-Type": "application/json"}, json=search_payload
    ).json()

    raydium_tokens = []
    if "result" in tokens_response and "items" in tokens_response["result"]:
        for item in tokens_response["result"]["items"]:
            token_address = item["id"]

        # Get token metadata including freeze authority
        token_info_payload = {
            "jsonrpc": "2.0",
            "id": "token-info",
            "method": "getAccountInfo",
            "params": [token_address, {"encoding": "jsonParsed"}],
        }

        token_info = requests.post(
            RPC_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json=token_info_payload,
        ).json()

        freeze_authority = token_info["result"]["value"]["data"]["parsed"]["info"].get(
            "freezeAuthority"
        )

        # Get top holders data
        holders_payload = {
            "jsonrpc": "2.0",
            "id": "token-holders",
            "method": "getProgramAccounts",
            "params": [
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                {
                    "filters": [
                        {"dataSize": 165},
                        {"memcmp": {"offset": 0, "bytes": token_address}},
                    ],
                    "encoding": "jsonParsed",
                },
            ],
        }

        holders = requests.post(
            RPC_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json=holders_payload,
        ).json()

        # Calculate top holders percentage
        total_supply = float(
            token_info["result"]["value"]["data"]["parsed"]["info"]["supply"]
        )
        sorted_holders = sorted(
            holders["result"],
            key=lambda x: float(
                x["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]
            ),
            reverse=True,
        )
        top_10_percentage = (
            sum(
                float(h["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
                for h in sorted_holders[:10]
            )
            / total_supply
            * 100
        )

        # Get DEX data including LP info
        dex_data = requests.get(f"{DEXSCREENER_API}/{token_address}").json()

        if "pairs" in dex_data:
            raydium_pairs = [
                pair for pair in dex_data["pairs"] if "raydium" in pair["dexId"].lower()
            ]
            if raydium_pairs:
                # Check LP token burn
                lp_address = raydium_pairs[0].get("pairAddress")
                lp_burned = "Yes" if check_lp_burn(lp_address) else "No"

                raydium_tokens.append(
                    {
                        "address": token_address,
                        "name": dex_data["pairs"][0].get("baseToken", {}).get("name"),
                        "symbol": dex_data["pairs"][0]
                        .get("baseToken", {})
                        .get("symbol"),
                        "price": dex_data["pairs"][0].get("priceUsd"),
                        "liquidity": dex_data["pairs"][0]
                        .get("liquidity", {})
                        .get("usd"),
                        "volume_24h": dex_data["pairs"][0].get("volume", {}).get("h24"),
                        "freeze_authority": freeze_authority,
                        "lp_burned": lp_burned,
                        "top_10_holders_pct": top_10_percentage,
                    }
                )

    return raydium_tokens


# Send Telegram alert
def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.get(url, params=params)

    print(message)


def monitor_creator_tokens(creator_address, config):
    dex_url = f"https://dexscreener.com/solana/{TOKEN_ADDRESS}"
    while True:
        creator_tokens = get_creator_tokens(creator_address)

        print(f"\n🔍 Found {len(creator_tokens)} tokens by creator on Raydium:")
        if not creator_tokens:
            print("💫 No tokens found for this creator yet. Continuing to monitor...")
            send_alert(
                "Creator has no tokens listed on Raydium yet. Will notify when new tokens are detected."
            )
        else:
            for token in creator_tokens:
                message = (
                    f"🪙 Token: {token['symbol']}\n"
                    f"💰 Price: ${token['price']}\n"
                    f"💧 Liquidity: ${token['liquidity']}\n"
                    f"📊 24h Volume: ${token['volume_24h']}\n"
                    f"🔒 Freeze Authority: {token['freeze_authority'] or 'None'}\n"
                    f"🔥 LP Burned: {token['lp_burned']}\n"
                    f"👥 Top 10 Holders: {token['top_10_holders_pct']:.2f}%"
                    f"🔗 DexScreener :{dex_url}"
                )
                print(message)
                send_alert(message)

        time.sleep(config.config["check_intervals"]["whales"])


# Monitor price changes
def monitor_price(initial_price, config):
    dex_url = f"https://dexscreener.com/solana/{TOKEN_ADDRESS}"
    while True:
        dex_data = requests.get(f"{DEXSCREENER_API}/{TOKEN_ADDRESS}").json()
        current_price = float(dex_data["pairs"][0]["priceUsd"])
        price_change = abs((current_price - initial_price) / initial_price) * 100

        if price_change > config.config["price_change_threshold"]:
            send_alert(
                f"🚨 Price Alert: {price_change:.2f}% change! "
                f"Current price: ${current_price}"
                f"DexScreener: {dex_url}"
            )

        time.sleep(config.config["check_intervals"]["price"])


# Monitor liquidity changes
def monitor_liquidity(initial_liquidity, config):
    dex_url = f"https://dexscreener.com/solana/{TOKEN_ADDRESS}"
    while True:
        dex_data = requests.get(f"{DEXSCREENER_API}/{TOKEN_ADDRESS}").json()
        current_liquidity = float(dex_data["pairs"][0]["liquidity"]["usd"])
        liquidity_change = (
            abs((current_liquidity - initial_liquidity) / initial_liquidity) * 100
        )

        if liquidity_change > config.config["liquidity_change_threshold"]:
            send_alert(
                f"🚨 Liquidity Alert: {liquidity_change:.2f}% change!"
                f"Current liquidity: ${current_liquidity}"
                f"DexScreener: {dex_url}"
            )

        time.sleep(config.config["check_intervals"]["liquidity"])


# Monitor whale activity
def monitor_whales(total_supply, config):
    while True:
        holders_payload = {
            "jsonrpc": "2.0",
            "id": "token-holders",
            "method": "getProgramAccounts",
            "params": [
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                {
                    "filters": [
                        {"dataSize": 165},
                        {"memcmp": {"offset": 0, "bytes": TOKEN_ADDRESS}},
                    ],
                    "encoding": "jsonParsed",
                },
            ],
        }

        holders_response = requests.post(
            RPC_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json=holders_payload,
        ).json()

        for holder in holders_response["result"]:
            balance = float(
                holder["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]
            )
            holder_address = holder["account"]["data"]["parsed"]["info"]["owner"]

            if balance > config.config["whale_threshold"] * total_supply:
                send_alert(
                    f"🐋 Whale Alert: {holder_address} holds {balance / total_supply * 100:.2f}% of supply!"
                )

        time.sleep(config.config["check_intervals"]["whales"])


# Monitor suspicious transactions
def monitor_transactions(total_supply, config):
    wallet_history = {}
    dex_url = f"https://dexscreener.com/solana/{TOKEN_ADDRESS}"

    while True:
        try:
            tx_payload = {
                "jsonrpc": "2.0",
                "id": "tx-history",
                "method": "getSignaturesForAddress",
                "params": [TOKEN_ADDRESS, {"limit": 100}],
            }

            tx_response = requests.post(
                RPC_ENDPOINT,
                headers={"Content-Type": "application/json"},
                json=tx_payload,
            ).json()

            if tx_response["result"]:
                for tx in tx_response["result"]:
                    tx_detail_payload = {
                        "jsonrpc": "2.0",
                        "id": "tx-detail",
                        "method": "getTransaction",
                        "params": [
                            tx["signature"],
                            {
                                "encoding": "jsonParsed",
                                "maxSupportedTransactionVersion": 0,
                            },
                        ],
                    }

                    tx_detail = requests.post(
                        RPC_ENDPOINT,
                        headers={"Content-Type": "application/json"},
                        json=tx_detail_payload,
                    ).json()

                    if "result" in tx_detail and tx_detail["result"]:
                        for account in tx_detail["result"]["transaction"]["message"][
                            "accountKeys"
                        ]:
                            wallet = account["pubkey"]
                            if wallet not in wallet_history:
                                wallet_history[wallet] = {
                                    "first_seen": datetime.now(),
                                    "last_seen": datetime.now(),
                                    "transaction_count": 1,
                                    "transactions": [],
                                }
                            else:
                                wallet_history[wallet]["last_seen"] = datetime.now()
                                wallet_history[wallet]["transaction_count"] += 1

                            wallet_history[wallet]["transactions"].append(
                                {
                                    "timestamp": datetime.now(),
                                    "signature": tx["signature"],
                                    "type": "transfer",
                                }
                            )

                            post_balances = (
                                tx_detail["result"]
                                .get("meta", {})
                                .get("postTokenBalances", [])
                            )
                            if post_balances:
                                amount = float(
                                    post_balances[0]
                                    .get("uiTokenAmount", {})
                                    .get("amount", 0)
                                )
                                if (
                                    amount
                                    > config.config["whale_threshold"] * total_supply
                                ):
                                    alert_message = (
                                        f"🚨 Large Transaction:\n"
                                        f"Wallet: {wallet}\n"
                                        f"Amount: {amount}\n"
                                        f"History: {wallet_history[wallet]['transaction_count']} transactions\n"
                                        f"DexScreener: {dex_url}"
                                    )
                                    send_alert(alert_message)

        except Exception as e:
            logging.error(f"Transaction monitoring error: {str(e)}")

        time.sleep(config.config["check_intervals"]["transactions"])


def monitor_market_cap(initial_price, total_supply, config):
    while True:
        dex_data = requests.get(f"{DEXSCREENER_API}/{TOKEN_ADDRESS}").json()
        current_price = float(dex_data["pairs"][0]["priceUsd"])

        initial_market_cap = initial_price * total_supply
        current_market_cap = current_price * total_supply
        market_cap_change = (
            abs((current_market_cap - initial_market_cap) / initial_market_cap) * 100
        )

        if market_cap_change > config.config["market_cap_change_threshold"]:
            send_alert(
                f"📊 Market Cap Alert:\n"
                f"Change: {market_cap_change:.2f}%\n"
                f"Current MC: ${current_market_cap:,.2f}\n"
                f"Current Price: ${current_price:,.6f}"
            )

        time.sleep(config.config["check_intervals"]["market_cap"])


# Main function
def main():
    setup_logging()
    logging.info("Starting whale monitoring system")

    config = MonitorConfig()
    health_check = HealthCheck()
    monitor_threads = MonitoringThreads()

    initial_data = fetch_initial_data()

    dex_url = f"https://dexscreener.com/solana/{TOKEN_ADDRESS}"

    print("\n🔎 Initial Token Analysis:")
    print(f"🪙 Token: {TOKEN_ADDRESS}")
    print(f"💰 Current Price: ${initial_data['price']}")
    print(f"💧 Liquidity: ${initial_data['liquidity']}")
    print(f"📊 Market Cap: ${initial_data['market_cap']}")
    print(f"📈 Total Supply: {initial_data['total_supply']}")
    if initial_data["creator_tokens"]:
        print(f"👤 Creator: {initial_data['creator_tokens'][0]['creator']}")
        print(
            f"💰 Creator Tokens: {initial_data['creator_tokens'][0]['creator_tokens']}"
        )
        print(f"🔥 LP Burned: {initial_data['creator_tokens'][0]['lp_burned']}")
        print(
            f"👥 Top 10 Holders: {initial_data['creator_tokens'][0]['top_10_holders_pct']:.2f}%"
        )
    else:
        print(f"No tokens found for creator {initial_data['creator']}")
    print(f"🔗 DexScreener: {dex_url}")

    monitor_threads.add_thread(monitor_price, (initial_data["price"], config))
    monitor_threads.add_thread(monitor_liquidity, (initial_data["liquidity"], config))
    monitor_threads.add_thread(monitor_whales, (initial_data["total_supply"], config))
    monitor_threads.add_thread(
        monitor_transactions, (initial_data["total_supply"], config)
    )
    monitor_threads.add_thread(
        monitor_market_cap,
        (initial_data["price"], initial_data["total_supply"], config),
    )
    monitor_threads.add_thread(
        monitor_creator_tokens, (initial_data["creator"], config)
    )

    try:
        while True:
            unhealthy = health_check.check_health()
            if unhealthy:
                logging.warning(f"Unhealthy monitors: {unhealthy}")
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Shutting down monitoring system")
        monitor_threads.shutdown()


if __name__ == "__main__":
    main()
