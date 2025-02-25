from pathlib import Path

# Constants - moved outside class for global use, consider a Config class
PAST_TOKENS_TO_SHOW = 30
CHECK_INTERVAL = 10
DISPLAY_DELAY = 0.5
ANIMATION_DURATION = 10
AUTO_OPEN_BROWSER = False
USE_DEXSCREENER = True
EXCLUDE_PATTERNS = ["So11111111111111111111111111111111111111112"]
BASE_URL = "http://api.moondev.com:8000"
SOUND_ENABLED = True
DATA_FOLDER = (
    Path(__file__).parent.parent.parent / "data" / "sniper_agent"
)  # Adjusted path

##########################################################################
# DEGEN PLAY SETTINGS:
#
# LIQUIDITY > 10000
# MIN MKT CAP 100000
# 24H VOLUME > 500000
# MAX AGE < 12
#
# MIDDLE RISK PLAY SETTINGS:
# 
# LIQUIDITY > 100000
# MIN MKT CAP 1000000
# 24H VOLUME > 5000000
# MIN AGE < 150MINS(2.5HRS)
# 
# LOW RISK PLAY SETTINGS:
#
# LIQUIDITY > 100000
# MIN MKT CAP 5000000
# 24H VOLUME > 15000000
# MIN AGE < 1800MINS(30HRS)
#
##########################################################################

# Analysis Constants
CHECK_INTERVAL = 600  # 5 minutes between each analysis run
MIN_MARKET_CAP = 1000  # Minimum market cap in USD
MAX_MARKET_CAP = 1000000  # Maximum market cap in USD (10M)
MIN_LIQUIDITY = 1000  # Minimum liquidity in USD
MAX_LIQUIDITY = 500000  # Maximum liquidity in USD (500k)
MIN_VOLUME_24H = 5000  # Minimum 24h volume
MAX_TOP_HOLDERS_PCT = 60  # Maximum percentage held by top 10 holders
MIN_UNIQUE_HOLDERS = 100  # Minimum number of unique holders
MIN_AGE_HOURS = 1  # Minimum token age in hours
MAX_AGE_HOURS = 48  # Maximum token age in hours
MIN_BUY_TX_PCT = 60  # Minimum percentage of buy transactions
MIN_TRADES_LAST_HOUR = 10  # Minimum number of trades in last hour

ATTENTION_EMOJIS = [
    "🚨",
    "💫",
    "⚡",
    "🔥",
    "✨",
    "💥",
    "🎯",
    "🎪",
    "🎢",
    "🎡",
    "🎠",
    "🌈",
    "🦄",
    "🌟",
    "💎",
    "🚀",
]
BACKGROUND_COLORS = [
    "on_blue",
    "on_magenta",
    "on_cyan",
    "on_red",
    "on_green",
    "on_yellow",
    "on_grey",
    "on_white",
]
LAUNCH_EMOJIS = [
    "🚀",
    "💎",
    "🌙",
    "⭐",
    "🔥",
    "💫",
    "✨",
    "🌟",
    "💰",
    "🎯",
    "🎆",
    "🌠",
    "⚡",
    "🌈",
    "🎨",
    "🎪",
    "🎭",
    "🎡",
    "🎢",
    "🎠",
    "🦁",
    "🐉",
    "🦊",
    "🦄",
    "🐋",
    "🦈",
    "🦅",
    "🦚",
    "🦜",
    "🦋",
    "🏆",
    "🎮",
    "🎲",
    "🎱",
    "🎳",
    "🎪",
    "🎨",
    "🎭",
    "🎪",
    "🎢",
    "🌍",
    "🌎",
    "🌏",
    "🌕",
    "🌖",
    "🌗",
    "🌘",
    "🌑",
    "🌒",
    "🌓",
    "💥",
    "🌪️",
    "⚡",
    "☄️",
    "🌠",
    "🎇",
    "🎆",
    "✨",
    "💫",
    "⭐",
]

ANALYSIS_EMOJIS = [
    "🔍",
    "📊",
    "📈",
    "🎯",
    "💎",  # Analysis & targets
    "🚀",
    "⭐",
    "🌟",
    "✨",
    "💫",  # Moon Dev specials
    "🎨",
    "🎭",
    "🎪",
    "🎢",
    "🎡",  # Fun stuff
]

SOUND_EFFECTS = [
    "moondev/src/audio/notification.mp3",
    "moondev/src/audio/ui-positive-selection-ni-sound-1-00-03.mp3",
]
