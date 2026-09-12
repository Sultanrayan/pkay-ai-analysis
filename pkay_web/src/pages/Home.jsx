import {
  Button,
  Card,
  CodeBlock,
  SectionHeading,
  StatCard,
} from "../components/ui.jsx";
import {
  AuroraBackground,
  GlowRing,
  Marquee,
  NumberTicker,
  Reveal,
  SpotlightCard,
} from "../components/premium.jsx";
import { StaggerTestimonials } from "../components/testimonials.jsx";
import { MODELS } from "../lib/models.js";

const stats = [
  {
    label: "AI agents",
    value: 10,
    hint: "Technical · Intel · Risk · Sniper",
  },
  { label: "Assets", value: 4, suffix: "+", hint: "BTC · ETH · SOL · XAU" },
  {
    label: "Avg. response",
    value: 320,
    prefix: "~",
    suffix: "ms",
    hint: "Cached & parallel",
  },
  {
    label: "Uptime",
    value: 99.9,
    decimals: 1,
    suffix: "%",
    hint: "Live + demo fallback",
  },
];

const features = [
  {
    title: "AI Agent Team",
    text: "Ten specialized agents across technical, market-intel and risk teams vote into one weighted consensus.",
  },
  {
    title: "Latest AI Model",
    text: "Enrichment is now handled by the latest AI Model, which refines the final signal with graceful deterministic fallback.",
  },
  {
    title: "Memecoin sniper",
    text: "Signal-only opportunity ranking with liquidity and safety checks. Never executes orders.",
  },
  {
    title: "Charts & indicators",
    text: "RSI, MACD, Bollinger, ATR, OBV and candlestick charts generated on every request.",
  },
  {
    title: "Multi-asset",
    text: "BTCUSDT, ETHUSDT, SOLUSDT and XAUUSD, plus cross-asset correlation.",
  },
  {
    title: "Risk management",
    text: "ATR-based stop-loss, take-profit and position sizing on every analysis.",
  },
];

const steps = [
  {
    step: "01",
    title: "Create an API key",
    text: "Open the dashboard and generate a key in seconds. Scope it per environment.",
  },
  {
    step: "02",
    title: "Send a Data Pair",
    text: "POST a symbol + timeframe to /api/v3/analyze. That pair is all the input we need.",
  },
  {
    step: "03",
    title: "Get the AI analysis",
    text: "Receive signal, confidence, agent scores, risk levels and a plain-English summary.",
  },
];

const sampleRequest = `curl -X POST https://api.pkay.ai/api/v3/analyze \\
  -H "Authorization: Bearer pk_live_..." \\
  -H "Content-Type: application/json" \\
  -d '{ "symbol": "BTCUSDT", "timeframe": "1h" }'`;

export default function Home() {
  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[680px] grid-lines opacity-40 [mask-image:linear-gradient(to_bottom,black,transparent)]" />

      {/* Hero */}
      <section className="relative mx-auto max-w-7xl px-4 pb-20 pt-16 sm:px-6 lg:px-8 lg:pt-24">
        <AuroraBackground className="-z-10" />
        <div className="grid items-center gap-16 lg:grid-cols-[1.1fr_0.9fr]">
          <Reveal>
            <p className="mb-6 text-sm font-semibold uppercase tracking-[0.2em] text-neutral-500">
              AI Agent Team · Analysis &amp; AI Model
            </p>
            <h1 className="text-4xl font-extrabold leading-[1.05] tracking-tight text-white sm:text-6xl">
              One endpoint.
              <br />
              <span className="text-shimmer">Every market insight.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-neutral-400">
              Pkay AI turns a single{" "}
              <span className="font-mono text-neutral-200">
                POST /api/v3/analyze
              </span>{" "}
              call into a full multi-agent trading report. Send a Data Pair and
              the AI Agent Team does the rest.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button to="/dashboard" size="lg">
                Create an API key
              </Button>
              <Button to="/how-it-works" variant="secondary" size="lg">
                See how it works
              </Button>
            </div>
          </Reveal>

          <Reveal delay={120} className="relative">
            <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-gradient-to-br from-white/5 via-transparent to-white/5 blur-2xl" />
            <SpotlightCard className="animate-float bg-black/60 p-4 shadow-2xl shadow-black">
              <div className="mb-3 flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-rose-400/80" />
                <span className="h-3 w-3 rounded-full bg-amber-400/80" />
                <span className="h-3 w-3 rounded-full bg-emerald-400/80" />
                <span className="ml-2 font-mono text-xs text-neutral-500">
                  request.sh
                </span>
              </div>
              <CodeBlock code={sampleRequest} language="bash" />
              <div className="mt-4 grid grid-cols-3 gap-3">
                {[
                  { k: "Signal", v: "BUY", tone: "text-emerald-400" },
                  { k: "Confidence", v: "82%", tone: "text-white" },
                  { k: "Score", v: "+58", tone: "text-neutral-200" },
                ].map((item) => (
                  <div
                    key={item.k}
                    className="rounded-xl border border-white/10 bg-white/[0.03] p-3"
                  >
                    <p className="text-xs text-neutral-500">{item.k}</p>
                    <p className={`text-lg font-bold ${item.tone}`}>{item.v}</p>
                  </div>
                ))}
              </div>
            </SpotlightCard>
          </Reveal>
        </div>

        {/* Stats */}
        <div className="mt-20 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat, index) => (
            <Reveal key={stat.label} delay={index * 80}>
              <StatCard
                label={stat.label}
                hint={stat.hint}
                value={
                  <NumberTicker
                    value={stat.value}
                    prefix={stat.prefix}
                    suffix={stat.suffix}
                    decimals={stat.decimals}
                  />
                }
              />
            </Reveal>
          ))}
        </div>
      </section>

      {/* Capability marquee */}
      <section className="border-y border-white/5 bg-white/[0.01] py-6">
        <Marquee
          items={MODELS.map((model) => ({
            label: model.name,
            logo: model.logo,
          }))}
        />
      </section>

      {/* Features */}
      <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <Reveal>
          <SectionHeading
            eyebrow="Why Pkay AI"
            title="Everything you need to read the market"
            subtitle="A production-grade analysis stack behind a single, predictable endpoint."
          />
        </Reveal>
        <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <Reveal key={feature.title} delay={(index % 3) * 90}>
              <SpotlightCard hover className="h-full p-6">
                <span className="font-mono text-sm text-neutral-600">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-4 text-lg font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-400">
                  {feature.text}
                </p>
              </SpotlightCard>
            </Reveal>
          ))}
        </div>
      </section>

      {/* How it works teaser */}
      <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <Reveal>
          <SectionHeading
            eyebrow="How it works"
            title="From key to insight in three steps"
            subtitle="No connectors, no Data Connect — just a Data Pair and an endpoint."
          />
        </Reveal>
        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {steps.map((step, index) => (
            <Reveal key={step.step} delay={index * 100} className="relative">
              <Card hover className="h-full">
                <span className="font-mono text-3xl font-bold text-white/15">
                  {step.step}
                </span>
                <h3 className="mt-5 text-lg font-semibold text-white">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-400">
                  {step.text}
                </p>
              </Card>
            </Reveal>
          ))}
        </div>
        <div className="mt-10 text-center">
          <Button to="/how-it-works" variant="secondary">
            Full walkthrough
          </Button>
        </div>
      </section>

      {/* Testimonials */}
      <section className="mx-auto max-w-7xl px-4 pb-24 sm:px-6 lg:px-8">
        <Reveal>
          <SectionHeading
            eyebrow="Testimonials"
            title="Builders ship faster with Pkay AI"
            subtitle="Teams of every size use the AI Agent Team to turn a single request into a full market read."
          />
        </Reveal>
        <Reveal delay={120}>
          <StaggerTestimonials />
        </Reveal>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-4 pb-8 sm:px-6 lg:px-8">
        <Reveal>
          <Card className="relative overflow-hidden border-white/10 bg-gradient-to-b from-white/[0.06] to-transparent p-10 text-center sm:p-16">
            <GlowRing />
            <div className="pointer-events-none absolute -right-10 -top-10 h-48 w-48 rounded-full bg-white/10 blur-3xl" />
            <h2 className="relative text-3xl font-bold text-white sm:text-4xl">
              Ready to call the AI Agent Team?
            </h2>
            <p className="relative mx-auto mt-4 max-w-xl text-neutral-400">
              Generate a key in the dashboard and send your first Data Pair in
              under a minute.
            </p>
            <div className="relative mt-8 flex flex-wrap justify-center gap-3">
              <Button to="/dashboard" size="lg">
                Open Dashboard
              </Button>
              <Button to="/docs" variant="secondary" size="lg">
                Read the Docs
              </Button>
            </div>
          </Card>
        </Reveal>
      </section>
    </div>
  );
}
