"""Deterministic simulated sources for on-chain, macro and sniper data.

The bot ships with no paid provider keys (Glassnode/Whale-Alert, economic
data feeds, DEX Screener/Raydium), so these modules produce **stable,
clearly-flagged heuristic values** that keep every report useful offline and
make tests deterministic. Every snapshot carries ``is_demo=True`` so reports
disclose the provenance; wiring a live feed later only means implementing the
same snapshot-returning methods elsewhere and swapping the instance in the
data manager.
"""

from __future__ import annotations

import random

from ..domain import MacroSnapshot, OnChainSnapshot, SniperScan, SniperToken, Symbol


class DemoOnChainSource:
    """Deterministic per-symbol on-chain heuristic (clearly flagged demo)."""

    def build(self, symbol: Symbol) -> OnChainSnapshot:
        rng = random.Random(f"onchain:{symbol.value}")
        return OnChainSnapshot(
            whale_activity=round(rng.uniform(-40.0, 70.0), 1),
            exchange_netflow=round(rng.uniform(-50.0, 60.0), 1),
            active_addresses=round(rng.uniform(-30.0, 50.0), 1),
            mvrv=round(rng.uniform(0.8, 3.2), 2),
            sopr=round(rng.uniform(0.9, 1.8), 3),
            is_demo=True,
        )


class DemoMacroSource:
    """Deterministic macro heuristic (clearly flagged demo)."""

    def build(self) -> MacroSnapshot:
        # Mildly risk-on baseline so the block stays readable; all values are
        # simulated until a real economic data feed is configured.
        return MacroSnapshot(
            rate_trend=0.3,
            dxy_trend=-0.2,
            inflation_trend=0.4,
            is_demo=True,
        )


#: Fixed demo roster so the sniper scan is stable across runs (a live DEX
#: Screener/Raydium feed would replace this with real, timestamped entries).
_DEMO_TOKENS: tuple[SniperToken, ...] = (
    SniperToken(
        symbol="PEPE_X",
        chain="solana",
        liquidity_usd=2_100_000.0,
        volume_5m_usd=1_400_000.0,
        hype_score=85.0,
        safety_score=92.0,
        launch_age_minutes=240,
        price_change_pct=18.4,
    ),
    SniperToken(
        symbol="MOONX",
        chain="ethereum",
        liquidity_usd=920_000.0,
        volume_5m_usd=410_000.0,
        hype_score=71.0,
        safety_score=74.0,
        launch_age_minutes=180,
        price_change_pct=9.7,
    ),
    SniperToken(
        symbol="DOGE2",
        chain="bsc",
        liquidity_usd=180_000.0,
        volume_5m_usd=90_000.0,
        hype_score=62.0,
        safety_score=34.0,
        launch_age_minutes=60,
        price_change_pct=42.1,
        risks=("liquidity not locked", "high sell tax"),
    ),
)


class DemoSniperScanner:
    """Signal-only memecoin scanner (demo roster, never executes orders)."""

    def scan(self) -> SniperScan:
        return SniperScan(tokens=_DEMO_TOKENS, source="demo", is_demo=True)