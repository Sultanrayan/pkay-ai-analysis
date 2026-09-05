"""Initialize the PostgreSQL schema.

Usage:
    python scripts/init_db.py                # uses DATABASE_URL from .env
    python scripts/init_db.py --url postgresql://user:pass@host:5432/db

Idempotent (CREATE TABLE IF NOT EXISTS) — safe to run repeatedly.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
from dotenv import load_dotenv

from tradingbot.config import ENV_FILE
from tradingbot.storage.repository import SCHEMA_PATH

DEFAULT_URL = "postgresql://tradingbot:tradingbot@localhost:5432/trading_bot"


async def init(url: str) -> None:
    ddl = SCHEMA_PATH.read_text(encoding="utf-8")
    connection = await asyncpg.connect(url)
    try:
        await connection.execute(ddl)
    finally:
        await connection.close()
    print(f"Schema applied to {url.split('@')[-1]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=None, help="PostgreSQL connection URL")
    args = parser.parse_args()

    load_dotenv(ENV_FILE)
    url = args.url or os.getenv("DATABASE_URL") or DEFAULT_URL
    asyncio.run(init(url))


if __name__ == "__main__":
    main()
