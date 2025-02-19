import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent.parent)  # Adjusted for streamlit subdir
if src_path not in sys.path:
    sys.path.append(src_path)

import time
import random
import requests
import pandas as pd
import logging
import re
from rich.console import Console
from termcolor import colored
from playsound import playsound
import streamlit as st  # Import streamlit
from streamlit_autorefresh import st_autorefresh
from config import *

# Suppress INFO logs
logging.getLogger().setLevel(logging.WARNING)

# Initialize Rich console
console = Console()


# 🛠️ Function to strip ANSI codes
def ansi_escape(text):
    """Remove all ANSI escape sequences from the text."""
    ansi_escape_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape_pattern.sub("", text).strip()


@st.cache_data  # Add Streamlit caching
def get_token_addresses(base_dir):
    """Fetch token data silently"""
    try:
        url = f"{BASE_URL}/files/new_token_addresses.csv"
        response = requests.get(url)
        response.raise_for_status()

        # Save to cache
        save_path = base_dir / "new_token_addresses.csv"
        with open(save_path, "wb") as f:
            f.write(response.content)

        df = pd.read_csv(save_path)
        return df

    except Exception as e:
        st.error(f"Error fetching token addresses: {e}")
        return None


class TokenScanner:
    def __init__(self):
        """🌙 Moon Dev's Token Scanner - Built with love by Moon Dev 🚀"""
        self.base_dir = (
            Path(__file__).parent.parent.parent / "api_data"
        )  # Adjusted path
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = DATA_FOLDER
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.seen_tokens = set()
        self.last_check_time = None
        self.sound_enabled = SOUND_ENABLED

        # Only check sound files if sound is enabled
        if self.sound_enabled:
            for sound_file in SOUND_EFFECTS:
                if not os.path.exists(sound_file):
                    print(f"⚠️ Warning: Sound file not found: {sound_file}")
                    self.sound_enabled = False
                    break

    def attention_animation(self):
        """Run an attention-grabbing animation"""
        start_time = time.time()
        position = 0
        direction = 1
        width = 40  # Animation width

        try:
            # Start on current line
            while time.time() - start_time < ANIMATION_DURATION:
                # Create animation frame
                emojis = random.sample(ATTENTION_EMOJIS, 3)  # Pick 3 random emojis
                spaces = " " * position
                color = random.choice(BACKGROUND_COLORS)

                # Print the animation frame with random colors
                print(
                    f'\r{spaces}{colored("".join(emojis), "white", color)}'
                    + " " * (width - position),
                    end="",
                    flush=True,
                )

                # Update position for bouncing effect
                position += direction
                if position >= width or position <= 0:
                    direction *= -1

                time.sleep(0.1)

            # Clear the animation line completely
            print("\r" + " " * (width + 20), end="\r", flush=True)

        except KeyboardInterrupt:
            # Clear line if interrupted
            print("\r" + " " * (width + 20), end="\r", flush=True)

    def filter_tokens(self, df):
        """Filter out unwanted tokens and sort by timestamp"""
        if df is None or df.empty:
            return pd.DataFrame()

        # Filter out tokens containing excluded patterns
        for pattern in EXCLUDE_PATTERNS:
            df = df[~df["Token Address"].str.contains(pattern, case=True)]

        # Sort by time found, oldest first
        return df.sort_values("Epoch Time", ascending=True)

    def get_display_link(self, birdeye_link):
        """Convert Birdeye link to DexScreener link if enabled"""
        if not USE_DEXSCREENER:
            return birdeye_link

        try:
            # Extract contract address from Birdeye link
            # Format: https://birdeye.so/token/CONTRACT_ADDRESS?chain=solana
            contract_address = birdeye_link.split("/token/")[1].split("?")[0]
            return f"https://dexscreener.com/solana/{contract_address}"
        except Exception:
            return birdeye_link

    def display_past_token(self, address, time_found, birdeye_link):
        """Display a past token with a placeholder to prevent UI flickering in Streamlit"""
        try:
            time_obj = pd.to_datetime(time_found)
            time_str = time_obj.strftime("%m-%d %H:%M")
        except Exception:
            time_str = ansi_escape(time_found)  # Remove potential ANSI artifacts

        random_emoji = random.choice(LAUNCH_EMOJIS)
        display_link = self.get_display_link(birdeye_link)

        # Create a placeholder to manage updates cleanly
        token_placeholder = st.empty()

        with token_placeholder.container():  # Ensures clean UI updates
            st.markdown(f"### {random_emoji} **NEW TOKEN FOUND!**")
            st.markdown(f"**Time Found:** {time_str}")
            st.markdown(f"[🔗 View on DexScreener]({display_link})")

        # Auto-open in browser if enabled
        if AUTO_OPEN_BROWSER:
            try:
                import webbrowser

                webbrowser.open(display_link)
            except Exception:
                pass

        time.sleep(DISPLAY_DELAY)

    def save_tokens_for_analysis(self, df):
        """Save tokens to CSV for analysis"""
        try:
            # Add timestamp column for when we saved this data
            df = df.copy()
            df.loc[:, "saved_at"] = pd.Timestamp.now()

            # Save to CSV
            save_path = self.data_dir / "recent_tokens.csv"
            df.to_csv(save_path, index=False)
        except Exception as e:
            st.error(f"Error saving tokens: {e}")

    def show_past_tokens(self):
        """Display past token launches"""
        df = get_token_addresses(self.base_dir)
        if df is None:
            st.warning("Could not fetch token data.")  # Streamlit warning
            return

        df = self.filter_tokens(df)

        if df.empty:
            st.info("No past tokens found.")
            return

        # Get the most recent tokens (from the end since we're sorted ascending)
        recent_tokens = df.tail(PAST_TOKENS_TO_SHOW)

        # Store seen tokens and last check time
        self.seen_tokens = set(recent_tokens["Token Address"])
        if not recent_tokens.empty:  # Check if recent_tokens is empty
            self.last_check_time = pd.to_datetime(recent_tokens.iloc[-1]["Time Found"])
        else:
            self.last_check_time = None  # Or some default value

        # Save tokens for analysis
        self.save_tokens_for_analysis(recent_tokens)

        st.subheader("🔍 Recent Token Launches")
        for _, row in recent_tokens.iterrows():
            self.display_past_token(
                row["Token Address"], row["Time Found"], row["Birdeye Link"]
            )

    def play_sound(self):
        """Play a random sound effect safely"""
        if not self.sound_enabled:
            return

        try:
            sound_file = random.choice(SOUND_EFFECTS)
            playsound(sound_file, block=False)
        except Exception as e:
            st.error(f"Error playing sound: {e}")  # Streamlit error

    def display_token(
        self, address: str, time_found: str, birdeye_link: str, is_new: bool = True
    ):
        """Display a token with Streamlit elements. Works for both new and past tokens."""
        try:
            time_obj = pd.to_datetime(time_found)
            time_str = time_obj.strftime("%m-%d %H:%M")
        except ValueError:
            time_str = ansi_escape(time_found)  # Clean potential ANSI artifacts

        random_emoji = random.choice(LAUNCH_EMOJIS)
        display_link = self.get_display_link(birdeye_link)

        # Create a placeholder for clean UI updates
        token_placeholder = st.empty()

        with token_placeholder.container():
            if is_new:
                st.markdown(f"### {random_emoji} **NEW TOKEN FOUND!**")
            st.markdown(f"**Address:** `{ansi_escape(address)}`")
            st.markdown(f"**Time:** {ansi_escape(time_str)}")
            st.markdown(f"[🔗 View on DexScreener]({ansi_escape(display_link)})")

        # Auto-open in browser if enabled (only for new tokens)
        if is_new and AUTO_OPEN_BROWSER:
            try:
                import webbrowser

                webbrowser.open(display_link)
            except Exception:
                pass

        time.sleep(DISPLAY_DELAY)

    def monitor_new_launches(self):
        """Monitor for new token launches and update UI correctly."""
        if "discovered_tokens" not in st.session_state:
            st.session_state["discovered_tokens"] = []  # Initialize session storage

        # Auto-refresh the page every CHECK_INTERVAL seconds
        st_autorefresh(interval=CHECK_INTERVAL * 1000, key="token_monitor")

        while True:
            try:
                df = get_token_addresses(self.base_dir)
                if df is None or df.empty:
                    time.sleep(CHECK_INTERVAL)
                    continue

                df = self.filter_tokens(df)
                if df.empty:
                    time.sleep(CHECK_INTERVAL)
                    continue

                current_time = pd.to_datetime(df.iloc[-1]["Time Found"])

                if self.last_check_time and current_time > self.last_check_time:
                    new_df = df[pd.to_datetime(df["Time Found"]) > self.last_check_time]
                    new_tokens = set(new_df["Token Address"]) - self.seen_tokens

                    if new_tokens:
                        new_token_rows = new_df[
                            new_df["Token Address"].isin(new_tokens)
                        ]

                        # Save to session state for UI updates
                        for _, row in new_token_rows.iterrows():
                            token_data = {
                                "address": row["Token Address"],
                                "time": row["Time Found"],
                                "link": row["Birdeye Link"],
                            }
                            if token_data not in st.session_state["discovered_tokens"]:
                                st.session_state["discovered_tokens"].append(token_data)

                            self.seen_tokens.add(row["Token Address"])

                        self.last_check_time = current_time

            except Exception as e:
                st.error(f"Monitoring error: {e}")

            time.sleep(CHECK_INTERVAL)


# Streamlit Interface
def main():
    """Main entry point"""
    scanner = TokenScanner()

    if st.button("Show Past Tokens"):
        scanner.show_past_tokens()

    if st.button("Start Monitoring New Launches"):
        st.write("🚀 Monitoring new token launches... (Keep this tab open)")
        scanner.monitor_new_launches()


if __name__ == "__main__":
    main()
