"""Development entry point: run the bot with long polling.

Usage:
    python bot.py

Requires TELEGRAM_BOT_TOKEN in .env (see .env.example). For production use
``webhook_server.py`` instead.
"""

from __future__ import annotations

import sys

from telegram import Update

from tradingbot.application import build_application
from tradingbot.config import Settings, setup_logging


def main() -> None:
    settings = Settings.from_env()
    setup_logging(settings.log_level)

    if not settings.telegram_bot_token or settings.telegram_bot_token.startswith("your_"):
        sys.exit(
            "No TELEGRAM_BOT_TOKEN configured. Copy .env.example to .env and "
            "add your token from @BotFather."
        )

    application = build_application(settings)
    print("Bot started in polling mode — press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
