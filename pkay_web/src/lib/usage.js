const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XAUUSD"];

function seeded(seed) {
  let value = seed;
  return () => {
    value = (value * 9301 + 49297) % 233280;
    return value / 233280;
  };
}

export function usageSeries(days = 14) {
  const rand = seeded(42);
  const out = [];
  const today = new Date();
  for (let i = days - 1; i >= 0; i -= 1) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    const weekend = [0, 6].includes(date.getDay());
    const base = weekend ? 120 : 260;
    const requests = Math.round(base + rand() * 220);
    out.push({
      date: date.toISOString().slice(5, 10),
      requests,
      analyses: Math.round(requests * 0.62),
      sniper: Math.round(requests * 0.24),
      errors: Math.round(requests * 0.02),
    });
  }
  return out;
}

export function symbolBreakdown(series) {
  const totals = SYMBOLS.map((symbol, index) => {
    const weight = [0.42, 0.27, 0.19, 0.12][index];
    const total = series.reduce((sum, day) => sum + day.requests, 0);
    return {
      symbol,
      requests: Math.round(total * weight),
    };
  });
  return totals;
}

export function usageSummary(series) {
  const total = series.reduce((sum, d) => sum + d.requests, 0);
  const today = series[series.length - 1]?.requests ?? 0;
  const yesterday = series[series.length - 2]?.requests ?? 0;
  const change =
    yesterday === 0 ? 0 : Math.round(((today - yesterday) / yesterday) * 100);
  const errors = series.reduce((sum, d) => sum + d.errors, 0);
  const successRate =
    total === 0 ? 100 : Number((((total - errors) / total) * 100).toFixed(1));
  return { total, today, change, successRate, errors };
}

export function recentRequests(count = 8) {
  const rand = seeded(7);
  const statuses = ["200", "200", "200", "200", "429", "200", "200", "401"];
  const rows = [];
  for (let i = 0; i < count; i += 1) {
    const symbol = SYMBOLS[Math.floor(rand() * SYMBOLS.length)];
    const status = statuses[Math.floor(rand() * statuses.length)];
    const date = new Date(Date.now() - i * 1000 * 60 * 37);
    rows.push({
      id: `req_${i}`,
      symbol,
      timeframe: ["1h", "4h", "1d"][Math.floor(rand() * 3)],
      status,
      latency: Math.round(180 + rand() * 420),
      at: date.toISOString(),
    });
  }
  return rows;
}

export function mockAnalysis({ symbol = "BTCUSDT", timeframe = "1h" } = {}) {
  const rand = seeded(symbol.length * 13 + timeframe.length * 7);
  const score = Math.round((rand() - 0.4) * 120);
  const signal = score > 15 ? "BUY" : score < -15 ? "SELL" : "HOLD";
  const price =
    symbol === "BTCUSDT"
      ? 64120.5
      : symbol === "ETHUSDT"
        ? 3420.8
        : symbol === "SOLUSDT"
          ? 178.4
          : 2380.1;
  return {
    symbol,
    timeframe,
    signal,
    score,
    confidence: Math.round(60 + rand() * 35),
    current_price: Number(price.toFixed(2)),
    agents: {
      technical: Number((score * 0.9).toFixed(1)),
      sentiment: Number((score * 0.5).toFixed(1)),
      onchain: Number((score * 0.4).toFixed(1)),
      macro: Number((score * 0.3).toFixed(1)),
      risk: Number((score * 0.7).toFixed(1)),
      sniper: Number((rand() * 100).toFixed(1)),
    },
    risk: {
      stop_loss: Number((price * 0.981).toFixed(2)),
      take_profit: Number((price * 1.031).toFixed(2)),
      position_size_pct: Number((1.5 + rand() * 2).toFixed(2)),
    },
    llm_enhanced: true,
    generated_at: new Date().toISOString(),
    summary:
      signal === "BUY"
        ? "Technical momentum is bullish, price is above the 50-period average and flows support continuation."
        : signal === "SELL"
          ? "Momentum has rolled over, price is below the 50-period average and risk conditions favour caution."
          : "Signals are mixed across agents; the model recommends waiting for confirmation.",
  };
}
