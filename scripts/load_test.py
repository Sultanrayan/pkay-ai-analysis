"""Quick in-process load test for the analysis pipeline.

Usage:
    python scripts/load_test.py --users 100 --requests 1000

Runs full end-to-end analyses (data manager + all agents + decision engine)
against the deterministic *demo* provider so no API keys, network or
infrastructure are required. Reports throughput and latency percentiles.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from tradingbot.analysis.runner import AnalysisRunner
from tradingbot.config import Settings
from tradingbot.data.manager import MarketDataManager
from tradingbot.domain import Symbol, Timeframe
from tradingbot.storage.ratelimit import MemoryRateLimiter
from tradingbot.storage.repository import InMemoryStorage

SYMBOLS = [Symbol.BTCUSD, Symbol.XAUUSD]
TIMEFRAMES = [Timeframe.H1, Timeframe.H4, Timeframe.D1]


async def run_load(users: int, requests: int) -> None:
    settings = Settings(use_demo_data=True, chart_enabled=False)
    client = httpx.AsyncClient()
    data = MarketDataManager(client, settings)
    runner = AnalysisRunner(data)
    storage = InMemoryStorage()
    await storage.connect()
    limiter = MemoryRateLimiter()

    latencies: list[float] = []
    started = time.perf_counter()
    for request_index in range(requests):
        user_id = 1000 + (request_index % users)
        symbol = SYMBOLS[request_index % len(SYMBOLS)]
        timeframe = TIMEFRAMES[(request_index // len(SYMBOLS)) % len(TIMEFRAMES)]
        await storage.get_or_create_user(user_id, language_code="en")
        status = await limiter.consume(user_id, settings.max_daily_requests)
        if not status.allowed:
            continue
        begin = time.perf_counter()
        await runner.analyze(symbol, timeframe)
        latencies.append((time.perf_counter() - begin) * 1000)
        await storage.register_analysis_request(user_id)

    elapsed = time.perf_counter() - started
    await client.aclose()
    await storage.close()

    if not latencies:
        print("No requests completed (check the rate limit).")
        return

    latencies.sort()
    percentiles = {
        "p50": latencies[len(latencies) // 2],
        "p90": latencies[int(len(latencies) * 0.9) - 1],
        "p99": latencies[int(len(latencies) * 0.99) - 1],
    }
    print(f"Completed {len(latencies)} analyses in {elapsed:.2f}s")
    print(f"Throughput: {len(latencies) / elapsed:.1f} analyses/sec")
    print(f"Latency avg: {statistics.mean(latencies):.0f} ms | "
          + " | ".join(f"{name}: {value:.0f} ms" for name, value in percentiles.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--users", type=int, default=100, help="Simulated users")
    parser.add_argument("--requests", type=int, default=1000, help="Total analysis requests")
    args = parser.parse_args()
    asyncio.run(run_load(args.users, args.requests))


if __name__ == "__main__":
    main()
