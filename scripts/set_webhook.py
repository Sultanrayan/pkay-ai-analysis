"""Register (or unregister) the bot webhook with Telegram.

Usage:
    python scripts/set_webhook.py --url https://bot.example.com/webhook
    python scripts/set_webhook.py --url ""          # remove the webhook
    python scripts/set_webhook.py --url ... --token YOUR_TOKEN
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from dotenv import load_dotenv

from tradingbot.config import ENV_FILE

API = "https://api.telegram.org"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Public HTTPS webhook URL or empty string")
    parser.add_argument("--token", default=None, help="Bot token (defaults to TELEGRAM_BOT_TOKEN)")
    args = parser.parse_args()

    load_dotenv(ENV_FILE)
    token = args.token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token or token.startswith("your_"):
        sys.exit("No valid bot token. Set TELEGRAM_BOT_TOKEN in .env or pass --token.")

    response = httpx.post(
        f"{API}/bot{token}/setWebhook",
        params={"url": args.url} if args.url else {"url": ""},
        timeout=15.0,
    )
    payload = response.json()
    if response.is_error or not payload.get("ok"):
        sys.exit(f"setWebhook failed ({response.status_code}): {payload}")
    print(payload.get("description", "Webhook updated"))


if __name__ == "__main__":
    main()
