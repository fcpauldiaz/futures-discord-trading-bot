import os
import re
from dotenv import load_dotenv

load_dotenv()

TICKER_SYMBOL = "MES"
GLOBAL_QUANTITY = int(os.getenv("GLOBAL_QUANTITY", "15"))
GLOBAL_REMAINING_QTY = 3

TOKEN = os.getenv("DISCORD_TOKEN", "")
TOKEN_2 = os.getenv("DISCORD_TOKEN_2", "")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")
CHANNEL_ID_2 = os.getenv("DISCORD_CHANNEL_ID_2", "")
API_URL = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=1"
API_URL_2 = f"https://discord.com/api/v9/channels/{CHANNEL_ID_2}/messages?limit=2"

GENERAL_CHANNEL_TOKEN = os.getenv("GENERAL_CHANNEL_TOKEN", "")
GENERAL_CHANNEL_ID = os.getenv("GENERAL_CHANNEL_ID", "")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

ORDER_FILE = "open_order.json"

PATTERN = re.compile(
    r"ES (long|short) (\d+): ([A-Z])(?:\s+\w+)?\s*.*Stop: (\d+)", re.IGNORECASE | re.DOTALL
)

TRIM_PATTERN = re.compile(
    r"#alert trim (\d+)/(\d+)", re.IGNORECASE
)

STOPPED_PATTERN = re.compile(
    r"#alert stopped", re.IGNORECASE
)

LONG_TRIGGERED_PATTERN = re.compile(
    r"Ticker: \*\*([^*]+)\*\*\s*\nInterval: \*\*(\d+)\*\*\s*\nLevel: \*\*([\d.]+)\*\*\s*\nScore: \*\*(\d+/\d+)\*\*\s*\nPrice: \*\*([\d.]+)\*\*\s*\nTime: \*\*([\d\s:-]+)\*\*",
    re.IGNORECASE | re.MULTILINE
)

TARGET_HIT_PATTERN = re.compile(
    r"Ticker: \*\*([^*]+)\*\*\s*\nInterval: \*\*(\d+)\*\*\s*\nLevel: \*\*([\d.]+)\*\*\s*\nTarget 1: \*\*([\d.]+)\*\*\s*\nEntry: \*\*([\d.]+)\*\*\s*\nProfit: \*\*([+-]?[\d.]+) pts\*\*\s*\nTime: \*\*([\d\s:-]+)\*\*",
    re.IGNORECASE | re.MULTILINE
)

TARGET2_HIT_PATTERN = re.compile(
    r"Ticker: \*\*([^*]+)\*\*\s*\nInterval: \*\*(\d+)\*\*\s*\nLevel: \*\*([\d.]+)\*\*\s*\nTarget 2: \*\*([\d.]+)\*\*\s*\nEntry: \*\*([\d.]+)\*\*\s*\nProfit: \*\*([+-]?[\d.]+) pts\*\*\s*\nTime: \*\*([\d\s:-]+)\*\*",
    re.IGNORECASE | re.MULTILINE
)

STOP_LOSS_PATTERN = re.compile(
    r"Stop Loss Hit\s*\nTicker: \*\*([^*]+)\*\*\s*\nInterval: \*\*(\d+)\*\*\s*\nLevel: \*\*([\d.]+)\*\*\s*\nEntry: \*\*([\d.]+)\*\*\s*\nExit: \*\*([\d.]+)\*\*\s*\nLoss: \*\*([+-]?[\d.]+) pts\*\*\s*\nTime: \*\*([\d\s:-]+)\*\*",
    re.IGNORECASE | re.MULTILINE
)

STOP_LOSS_SIMPLE_PATTERN = re.compile(
    r"Ticker: \*\*([^*]+)\*\*\s*\nInterval: \*\*(\d+)\*\*\s*\nLevel: \*\*([\d.]+)\*\*\s*\nEntry: \*\*([\d.]+)\*\*\s*\nExit: \*\*([\d.]+)\*\*\s*\nLoss: \*\*([+-]?[\d.]+) pts\*\*",
    re.IGNORECASE | re.MULTILINE
)

TRADING_MODE = os.getenv("TRADING_MODE", "paper")
