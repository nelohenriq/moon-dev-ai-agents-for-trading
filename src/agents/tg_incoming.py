import json
import asyncio
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from telethon import TelegramClient, events

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Telegram API credentials
API_ID = "24884181"  # Replace with your actual API ID
API_HASH = "12bac054343a2cd4302ba3c08390ae8a"  # Replace with your actual API Hash
CHANNEL_USERNAME = "https://t.me/solanatokensnew"  # Example: "@yourchannel"
SESSION_NAME = "telegram_listener"

# Directory to save messages
DATA_DIR = Path("moondev/src/data/telegram_posts")
DATA_DIR.mkdir(parents=True, exist_ok=True)


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


def save_message(message_data):
    """Saves messages in a single structured JSON file."""
    file_path = DATA_DIR / "telegram_messages.json"

    # Read existing data or create new structure
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

    content_parser = MessageContent(message_data["text"])

    # Create the full data structure
    data = {
        "metadata": {
            "source": "telegram",
            "channel": CHANNEL_USERNAME,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_messages": len(messages) + 1,
        },
        "messages": messages
        + [
            {
                "message_id": message_data["message_id"],
                "date": message_data["date"],
                "content": content_parser.parse(),
            }
        ],
    }

    # Save the complete structure
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"✅ Message {message_data['message_id']} added to collection.")
    except Exception as e:
        logging.error(f"Failed to save message: {e}")


async def main():
    """Fetches messages from the Telegram channel."""
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        logging.info("Listening for messages...")

        @client.on(events.NewMessage(chats=CHANNEL_USERNAME))
        async def handler(event):
            message = event.message
            message_data = {
                "message_id": message.id,
                "text": message.text,
                "date": str(message.date),
            }
            save_message(message_data)

        await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())