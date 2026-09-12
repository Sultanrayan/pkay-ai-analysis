import {
  Button,
  Card,
  SectionHeading,
} from "../components/ui.jsx";

const groups = [
  {
    title: "AI Analysis",
    items: [
      {
        title: "10-agent consensus",
        text: "Technical, intel, risk and sniper agents vote into one weighted signal.",
      },
      {
        title: "Latest AI Model",
        text: "Enrichment by the latest AI Model with deterministic fallback so reports always resolve.",
      },
      {
        title: "Full indicator suite",
        text: "RSI, MACD, Bollinger, ATR, OBV, moving averages and support/resistance.",
      },
    ],
  },
  {
    title: "Market coverage",
    items: [
      {
        title: "Multi-asset",
        text: "BTCUSDT, ETHUSDT, SOLUSDT and XAUUSD out of the box.",
      },
      {
        title: "Cross-asset correlation",
        text: "BTC↔XAU and ETH↔SOL return correlation on every report.",
      },
      {
        title: "Memecoin sniper",
        text: "Signal-only opportunity ranking with liquidity and safety filters.",
      },
    ],
  },
  {
    title: "Platform",
    items: [
      {
        title: "Key-scoped access",
        text: "Create, scope and revoke keys from the dashboard in seconds.",
      },
      {
        title: "Rate limiting",
        text: "Per-user daily caps with Redis or in-memory fallback.",
      },
      {
        title: "Usage analytics",
        text: "Live graphs of requests, analyses, errors and per-asset volume.",
      },
    ],
  },
];

const comparison = [
  ["Data Connect setup", "Required", "None"],
  ["Time to first call", "Hours", "Under a minute"],
  ["Agents", "Single model", "10-agent team"],
  ["Assets", "1", "4+"],
  ["Risk levels", "Manual", "ATR-based, automatic"],
  ["Sniper safety checks", "—", "Built in (signal-only)"],
];

export default function Features() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <SectionHeading
        eyebrow="Features"
        title="Built for serious market analysis"
        subtitle="Everything Pkay AI does behind POST /api/v3/analyze — no connectors, no manual wiring."
      />

      <div className="mt-16 space-y-16">
        {groups.map((group) => (
          <div key={group.title}>
            <div className="mb-6 flex items-center gap-4">
              <h2 className="text-2xl font-bold text-white">{group.title}</h2>
              <span className="h-px flex-1 bg-white/10" />
            </div>
            <div className="grid gap-6 md:grid-cols-3">
              {group.items.map((item, index) => (
                <Card key={item.title} hover className="group">
                  <span className="font-mono text-sm text-neutral-600">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h3 className="mt-4 font-semibold text-white">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-neutral-400">
                    {item.text}
                  </p>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Comparison */}
      <section className="mt-24">
        <SectionHeading
          eyebrow="Comparison"
          title="No Data Connect, by design"
          subtitle="Pkay AI replaces connector sprawl with one predictable endpoint."
        />
        <Card className="mx-auto mt-12 max-w-3xl overflow-hidden p-0">
          <div className="grid grid-cols-3 border-b border-white/10 bg-white/[0.03] px-6 py-4 text-sm font-semibold">
            <span className="text-neutral-400">Capability</span>
            <span className="text-center text-neutral-400">Legacy</span>
            <span className="text-center text-white">Pkay AI</span>
          </div>
          {comparison.map(([label, legacy, pkay], index) => (
            <div
              key={label}
              className={`grid grid-cols-3 px-6 py-4 text-sm ${
                index % 2 ? "bg-white/[0.02]" : ""
              }`}
            >
              <span className="text-neutral-300">{label}</span>
              <span className="text-center text-neutral-500">{legacy}</span>
              <span className="text-center font-medium text-emerald-300">
                {pkay}
              </span>
            </div>
          ))}
        </Card>
      </section>

      <div className="mt-20 flex flex-wrap justify-center gap-3">
        <Button to="/dashboard" size="lg">
          Get started free
        </Button>
        <Button to="/pricing" variant="secondary" size="lg">
          See pricing
        </Button>
      </div>
    </div>
  );
}
