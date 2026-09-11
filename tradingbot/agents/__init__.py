"""Analysis agents (V3: 10 specialized agents + decision engine).

Each agent owns one analytical dimension and returns a frozen result object
(see :mod:`.base`) with a directional score in -100..+100 (the sniper uses a
0..100 opportunity scale because it is informational only):

* :mod:`.technical`   — trend & momentum (RSI / MACD / moving averages)
* :mod:`.volume`      — OBV direction and volume participation
* :mod:`.volatility`  — Bollinger regime: band position, squeeze, ATR
* :mod:`.pattern`     — local breakout / support-resistance structure
* :mod:`.sentiment`   — news headlines, Fear & Greed, social volume
* :mod:`.onchain`     — whale activity, exchange flows, MVRV/SOPR
* :mod:`.macro`       — rates, dollar and inflation backdrop
* :mod:`.risk`        — ATR volatility, stop-loss/take-profit, position size
* :mod:`.correlation` — cross-asset return correlation (BTC<->XAU, ETH<->SOL)
* :mod:`.sniper`      — signal-only memecoin opportunity scan (never executes)
* :mod:`.decision`    — team-weighted consensus + confidence

Agents are pure functions of their inputs (the runner fetches data), which
keeps them unit testable without network or database access.
"""
