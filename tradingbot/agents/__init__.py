"""Analysis agents.

Each agent owns one analytical dimension and returns a frozen result object
(see :mod:`.base`) with a directional score in -100..+100:

* :mod:`.technical`   — RSI / MACD / moving averages / support-resistance
* :mod:`.sentiment`   — news headlines, Fear & Greed, social volume
* :mod:`.risk`        — ATR volatility, stop-loss/take-profit, position size
* :mod:`.correlation` — BTCUSD <-> XAUUSD return correlation
* :mod:`.decision`    — combines the four into a signal

Agents are pure functions of their inputs (the runner fetches data), which
keeps them unit testable without network or database access.
"""
