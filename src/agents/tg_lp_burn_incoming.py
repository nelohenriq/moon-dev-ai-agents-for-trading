import json
import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from telethon import TelegramClient, events

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Telegram API credentials
API_ID = "24884181"
API_HASH = "12bac054343a2cd4302ba3c08390ae8a"
NEW_TOKENS_CHANNEL = "https://t.me/solanatokensnew"
LP_BURN_CHANNEL = "https://t.me/solanaburns"  # Replace with actual LP burn channel

# Directories to save messages
NEW_TOKENS_DIR = Path("moondev/src/data/telegram_posts/new_tokens")
LP_BURN_DIR = Path("moondev/src/data/telegram_posts/lp_burn")
NEW_TOKENS_DIR.mkdir(parents=True, exist_ok=True)
LP_BURN_DIR.mkdir(parents=True, exist_ok=True)

class LpBurnMessageContent:
    def __init__(self, raw_text: str):
        self.raw_text = raw_text

    def parse(self):
        lines = self.raw_text.split('\n')
        data = {
            "token_name": self._extract_token_name(lines[0]),
            "burn_percentage": self._extract_value("🔥 Burn Percentage:", lines),
            "trading_start_time": self._parse_trading_start_time(lines),
            "marketcap": self._extract_value("📊 Marketcap:", lines),
            "liquidity": self._extract_value("💧 Liquidity:", lines),
            "price": self._extract_value("💵 Price:", lines),
            "launch_mc": self._extract_value("🚀 Launch MC:", lines),
            "total_supply": self._extract_value("📦 Total Supply:", lines),
            "security": self._extract_security(lines),
            "top_holders": self._extract_top_holders(lines),
            "score": self._extract_score(lines),
            "issues": self._extract_issues(lines),
            "links": self._extract_links(lines),
            "token_address": self._extract_token_address(self.raw_text)
        }
        return data

    def _extract_token_name(self, first_line):
        """Extracts the token name from the first line, removing markdown."""
        match = re.search(r'\*\*(.*?)\*\*|\((.*?)\)', first_line)
        if match:
            return match.group(1) or match.group(2)  # Return the non-null group
        return first_line.strip()  # If no markdown, return the stripped line

    def _extract_value(self, key, lines):
        for line in lines:
            if key in line:
                parts = line.split(key)
                if len(parts) > 1:
                    return parts[1].strip()
        return None

    def _parse_trading_start_time(self, lines):
        for line in lines:
            if "🕒 Trading Start Time:" in line:
                time_str = line.split("🕒 Trading Start Time:")[1].strip()
                try:
                    seconds = int(time_str.split()[0])
                    now = datetime.now(timezone.utc)  # Timezone-aware
                    start_time = now - timedelta(seconds=seconds)
                    return start_time.isoformat()
                except (ValueError, IndexError):
                    logging.warning("Failed to parse trading start time.")
                    return None
        return None

    def _extract_security(self, lines):
        security = {}
        for line in lines:
            if "Mutable Metadata:" in line:
                security["mutable_metadata"] = "Yes" not in line
            elif "Mint Authority:" in line:
                security["mint_authority"] = "No" in line
            elif "Freeze Authority:" in line:
                security["freeze_authority"] = "No" in line
        return security

    def _extract_top_holders(self, lines):
        top_holders = []
        top_holder_start = False
        for line in lines:
          if line.startswith("🏦 Top Holders:"):
            top_holder_start = True
            continue
          if top_holder_start and (line.startswith('├') or line.startswith('└')):
            parts = line.split('|')
            if len(parts) == 3:  # Ensure the line has the expected format
              try:
                holder = {
                    "address": re.search(r'\((.*?)\)', parts[0]).group(1) if re.search(r'\((.*?)\)', parts[0]) else None,
                    "amount": parts[1].strip(),
                    "percentage": parts[2].strip()
                }
                top_holders.append(holder)
              except Exception as e:
                logging.warning(f"Error parsing top holder line: {line}. Error: {e}")
          elif top_holder_start and not (line.startswith('├') or line.startswith('└')):
            break
        return top_holders

    def _extract_score(self, lines):
        for line in lines:
            if "🧠 Score:" in line:
                return line.split("🧠 Score:")[1].strip()
        return None

    def _extract_issues(self, lines):
        issues = []
        for line in lines:
            if line.startswith('🟥') or line.startswith('🟧'):
                issues.append(line.strip())
        return issues

    def _extract_links(self, lines):
        links = {}
        for line in lines:
            if "Solscan" in line:
                match = re.search(r'\((.*?)\)', line)
                if match:
                    links["solscan"] = match.group(1)
            elif "Birdeye" in line:
                match = re.search(r'\((.*?)\)', line)
                if match:
                    links["birdeye"] = match.group(1)
            elif "Dexscreener" in line:
                match = re.search(r'\((.*?)\)', line)
                if match:
                    links["dexscreener"] = match.group(1)
            elif "Photon" in line:
                match = re.search(r'\((.*?)\)', line)
                if match:
                    links["photon"] = match.group(1)
        return links

    def _extract_token_address(self, raw_text):
        match = re.search(r"`(.*?)`", raw_text)
        return match.group(1) if match else None

class MessageContent:
    def __init__(self, raw_text: str):
        self.raw_text = raw_text

    def parse(self):
        """Parse raw text into structured data."""
        lines = self.raw_text.split("\n")

        return {
            "token": {
                "name": self._extract_between_stars(lines[0]),
                "description": (
                    self._extract_between_stars(lines[2]) if len(lines) > 2 else ""
                ),
                "type": self._extract_after_colon(lines[4]) if len(lines) > 4 else "",
                "supply": self._extract_after_colon(lines[5]) if len(lines) > 5 else "",
                "address": self._extract_code_block(self.raw_text),
            },
            "deployer": {
                "address": self._extract_deployer_address(self.raw_text),
                "balance": self._extract_deployer_balance(self.raw_text),
            },
            "links": self._extract_links(self.raw_text),
            "raw_text": self.raw_text,
        }

    def _extract_between_stars(self, text: str) -> str:
        """Extract text between ** markers."""
        parts = text.split("**")
        return parts[1] if len(parts) > 1 else ""

    def _extract_after_colon(self, text: str) -> str:
        """Extract text after ':' and remove spaces."""
        return text.split(":")[-1].strip()

    def _extract_code_block(self, text: str) -> str:
        """Extract text inside `code` format."""
        parts = text.split("`")
        return parts[1] if len(parts) > 1 else ""

    def _extract_deployer_address(self, text: str) -> str:
        """Extract deployer wallet address from markdown link format."""
        match = re.search(
            r"\[(.*?)\]\(https://solscan.io/account/([a-zA-Z0-9]+)\)", text
        )
        return match.group(2) if match else ""

    def _extract_deployer_balance(self, text: str) -> str:
        """Extract deployer balance from last line of deployer section."""
        match = re.search(r"└ ([0-9.]+) SOL", text)
        return match.group(1) if match else "0"

    def _extract_links(self, text: str) -> dict:
        """Extract all links from the message."""
        links = {}
        if "Solscan" in text:
            solscan_url = self._extract_url(text, "Solscan")
        if "Birdeye" in text:
            links["birdeye"] = self._extract_url(text, "Birdeye")
        if "Photon" in text:
            links["photon"] = self._extract_url(text, "Photon")
        return links

    def _extract_url(self, text: str, platform: str) -> str:
        """Extract URL for specific platform."""
        start = text.find(platform)
        if start == -1:
            return ""
        url_start = text.find("https://", start)
        url_end = text.find(" ", url_start)
        return text[url_start : url_end if url_end != -1 else None]

async def new_tokens_listener(client):
    @client.on(events.NewMessage(chats=NEW_TOKENS_CHANNEL))
    async def new_tokens_handler(event):
        message = event.message
        message_data = {
            "message_id": message.id,
            "text": message.text,
            "date": str(message.date),
            "channel": NEW_TOKENS_CHANNEL,
        }
        content_parser = MessageContent
        parsed_content = content_parser(message_data["text"]).parse() # Parse here!!!
        message_data["content"] = parsed_content # And Save it here
        await save_message(message_data, NEW_TOKENS_DIR / "new_tokens_messages.json")

async def lp_burn_listener(client):
    @client.on(events.NewMessage(chats=LP_BURN_CHANNEL))
    async def lp_burn_handler(event):
        message = event.message
        message_data = {
            "message_id": message.id,
            "text": message.text,
            "date": str(message.date),
            "channel": LP_BURN_CHANNEL,
        }
        content_parser = LpBurnMessageContent
        parsed_content = content_parser(message_data["text"]).parse() #Parse here!!!
        message_data["content"] = parsed_content # And Save it here
        await save_message(message_data, LP_BURN_DIR / "lp_burn_messages.json")

async def save_message(message_data, file_path):
    """Saves messages in a single structured JSON file."""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                messages = data.get("messages", [])
            except json.JSONDecodeError:
                logging.warning("JSON file corrupted, starting fresh.")
                messages = []
    else:
        messages = []

    data = {
        "metadata": {
            "source": "telegram",
            "channel": message_data["channel"],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_messages": len(messages) + 1,
        },
        "messages": messages + [{
            "message_id": message_data["message_id"],
            "date": message_data["date"],
            "content": message_data["content"],
        }],
    }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"✅ Message {message_data['message_id']} added to collection.")
    except Exception as e:
        logging.error(f"Failed to save message: {e}")

async def main():
    async with TelegramClient("new_tokens_session", API_ID, API_HASH) as new_tokens_client, \
               TelegramClient("lp_burn_session", API_ID, API_HASH) as lp_burn_client:
        
        logging.info("Listening for messages...")

        new_tokens_task = asyncio.create_task(new_tokens_listener(new_tokens_client))
        lp_burn_task = asyncio.create_task(lp_burn_listener(lp_burn_client))

        await asyncio.gather(
            new_tokens_client.run_until_disconnected(),
            lp_burn_client.run_until_disconnected(),
            new_tokens_task,
            lp_burn_task
        )

if __name__ == "__main__":
    asyncio.run(main())
