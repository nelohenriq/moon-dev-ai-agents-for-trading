import streamlit as st
import time
import random
import pandas as pd
import requests
from pathlib import Path

# Constants
PAST_TOKENS_TO_SHOW = 20  # Number of past token launches to display
CHECK_INTERVAL = 10  # Seconds between each check for new launches
DISPLAY_DELAY = 0.5  # Seconds between displaying each token
ANIMATION_DURATION = 10  # Seconds to show attention-grabbing animation
AUTO_OPEN_BROWSER = False  # Set to True to automatically open new tokens in browser
USE_DEXSCREENER = True  # Set to True to use DexScreener instead of Birdeye
EXCLUDE_PATTERNS = [
    "So11111111111111111111111111111111111111112"
]  # Exclude the SOLE token pattern
BASE_URL = "http://api.moondev.com:8000"
SOUND_ENABLED = True  # Set to True to enable sound effects, False to disable them
DATA_FOLDER = Path(__file__).parent.parent / "data" / "sniper_agent"

# Emojis and Background Colors
ATTENTION_EMOJIS = ["🚨", "💫", "⚡", "🔥", "✨", "💥", "🌈", "🦄", "🌟", "💎", "🚀"]
LAUNCH_EMOJIS = ["🚀", "💎", "🌙", "⭐", "🔥", "💫", "✨", "🌟", "💰", "🎯"]

st.title("🌙 Moon Dev's Token Scanner 🚀")
st.write("Watches for new Solana token launches and displays them dynamically!")


@st.cache_data
def get_token_addresses():
    """Fetch token data."""
    try:
        url = f"{BASE_URL}/files/new_token_addresses.csv"
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(pd.compat.StringIO(response.text))
        return df
    except Exception:
        return None


def filter_tokens(df):
    """Filter and sort tokens."""
    if df is None or df.empty:
        return pd.DataFrame()
    for pattern in EXCLUDE_PATTERNS:
        df = df[~df["Token Address"].str.contains(pattern, case=True)]
    return df.sort_values("Epoch Time", ascending=True)


def get_display_link(birdeye_link):
    """Convert Birdeye link to DexScreener link."""
    if not USE_DEXSCREENER:
        return birdeye_link
    try:
        contract_address = birdeye_link.split("/token/")[1].split("?")[0]
        return f"https://dexscreener.com/solana/{contract_address}"
    except Exception:
        return birdeye_link


def display_token(row):
    """Display a new token with animation."""
    time_str = pd.to_datetime(row["Time Found"]).strftime("%m-%d %H:%M")
    display_link = get_display_link(row["Birdeye Link"])
    random_emoji = random.choice(LAUNCH_EMOJIS)

    st.markdown(f"### {random_emoji} NEW TOKEN FOUND at {time_str}")
    st.markdown(f"🔗 [View on DexScreener]({display_link})")
    st.markdown("---")

    for _ in range(5):
        st.write(random.choice(ATTENTION_EMOJIS) * 10)
        time.sleep(0.3)


def show_past_tokens():
    """Display past token launches."""
    df = get_token_addresses()
    df = filter_tokens(df)
    if df.empty:
        st.warning("No past tokens found.")
        return
    st.subheader("🔍 Recent Token Launches")
    for _, row in df.tail(PAST_TOKENS_TO_SHOW).iterrows():
        display_token(row)


def monitor_new_launches():
    """Continuously check for new launches."""
    last_check_time = None
    seen_tokens = set()
    while True:
        df = get_token_addresses()
        if df is not None:
            df = filter_tokens(df)
            if not df.empty:
                current_time = pd.to_datetime(df.iloc[-1]["Time Found"])
                if last_check_time is None or current_time > last_check_time:
                    new_df = df[pd.to_datetime(df["Time Found"]) > last_check_time]
                    new_tokens = set(new_df["Token Address"]) - seen_tokens
                    if new_tokens:
                        for _, row in new_df[
                            new_df["Token Address"].isin(new_tokens)
                        ].iterrows():
                            display_token(row)
                            seen_tokens.add(row["Token Address"])
                        last_check_time = current_time
        time.sleep(CHECK_INTERVAL)


if st.button("Show Past Tokens"):
    show_past_tokens()

if st.button("Start Monitoring New Launches"):
    st.write("🚀 Monitoring new token launches... (Keep this tab open)")
    monitor_new_launches()
