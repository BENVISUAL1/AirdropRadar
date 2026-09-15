import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def _env(name, default=None):
    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip()

    if value == "":
        return default

    return value


def _env_int(name, default):
    value = _env(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"{name} must be an integer, got {value!r}"
        ) from error


TELEGRAM_BOT_TOKEN = _env("TELEGRAM_BOT_TOKEN", "")

_raw_database_name = _env("DATABASE_NAME", "airdrops.db")
_database_path = Path(_raw_database_name)

if _database_path.is_absolute():
    DATABASE_NAME = str(_database_path)
else:
    DATABASE_NAME = str(BASE_DIR / _database_path)

ALERT_THRESHOLD = _env_int("ALERT_THRESHOLD", 60)
SCAN_INTERVAL = _env_int("SCAN_INTERVAL", 1800)

# Non-secret app config stays in code.
SOURCES = [
    "https://cointelegraph.com/rss",
    "https://airdropalert.com/feed/rssfeed",
    "https://coinmarketcap.com/community/rss/",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://www.theblock.co/rss.xml",
]


def require_bot_token():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing. "
            "Copy .env.example to .env and set your bot token."
        )

    if TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is still the placeholder. "
            "Set your real token in .env."
        )

    return TELEGRAM_BOT_TOKEN
