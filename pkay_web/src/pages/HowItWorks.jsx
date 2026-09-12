import {
  Badge,
  Button,
  Card,
  CodeBlock,
  SectionHeading,
} from "../components/ui.jsx";

const steps = [
  {
    step: "01",
    title: "Create an API key in the dashboard",
    text: "Sign in and generate a key. Keys are scoped to an environment (live or test) and can be revoked at any time.",
    code: `# .env
Pkay_API_KEY=pk_live_xxxxxxxxxxxxxxxxxxxx`,
  },
  {
    step: "02",
    title: "Send a request with a Data Pair",
    text: "Every request must include a Data Pair — the symbol and timeframe you want analysed. There is no Data Connect to wire up.",
    code: `curl -X POST https://api.pkay.ai/api/v3/analyze \\
  -H "Authorization: Bearer $Pkay_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{ "symbol": "ETHUSDT", "timeframe": "4h" }'`,
  },
  {
    step: "03",
    title: "The AI Agent Team runs",
    text: "Ten agents analyse technicals, sentiment, on-chain, macro, correlation and risk in parallel, then vote into a weighted consensus.",
    code: `// response (truncated)
{
  "signal": "BUY",
  "score": 58,
  "confidence": 82,
  "agents": { "technical": 58.0, "sentiment": 24.0, ... },
  "risk": { "stop_loss": 62900.0, "take_profit": 66100.0 }
}`,
  },
  {
    step: "04",
    title: "Consume the AI Model output",
    text: "Use the signal, confidence, agent scores and summary in your app, bot or dashboard. The latest AI Model enriches the final call when configured.",
    code: `{
  "llm_enhanced": true,
  "summary": "Technical momentum is bullish..."
}`,
  },
];

const teams = [
  {
    name: "Technical",
    weight: "35%",
    agents: ["technical", "volume", "volatility", "pattern"],
    tone: "brand",
  },
  {
    name: "Market Intel",
    weight: "25%",
    agents: ["sentiment", "onchain", "macro", "correlation"],
    tone: "accent",
  },
  {
    name: "Risk",
    weight: "20%",
    agents: ["risk"],
    tone: "green",
  },
  {
    name: "Sniper",
    weight: "Info",
    agents: ["sniper"],
    tone: "amber",
  },
];

export default function HowItWorks() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="max-w-3xl">
        <p className="mb-5 text-sm font-semibold uppercase tracking-[0.2em] text-neutral-500">
          How it works
        </p>
        <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
          One call to the <span className="text-gradient">AI Agent Team</span>
        </h1>
        <p className="mt-5 text-lg leading-relaxed text-neutral-400">
          Pkay AI has two features — Analysis and AI Model. Both are reached
          through a single endpoint, and both require a Data Pair. Here is the
          full lifecycle.
        </p>
      </div>

      {/* Steps */}
      <div className="mt-16 space-y-8">
        {steps.map((step) => (
          <Card
            key={step.step}
            className="grid gap-8 lg:grid-cols-2 lg:items-center"
          >
            <div>
              <p className="font-mono text-sm font-semibold text-neutral-500">
                STEP {step.step}
              </p>
              <h2 className="mt-4 text-2xl font-bold text-white">
                {step.title}
              </h2>
              <p className="mt-3 leading-relaxed text-neutral-400">
                {step.text}
              </p>
            </div>
            <CodeBlock code={step.code} language="bash" />
          </Card>
        ))}
      </div>

      {/* Data Pair */}
      <section className="mt-24">
        <SectionHeading
          eyebrow="The input"
          title="What is a Data Pair?"
          subtitle="A Data Pair is the symbol and timeframe that defines exactly what the AI Agent Team should analyse."
        />
        <div className="mx-auto mt-12 grid max-w-4xl gap-6 md:grid-cols-2">
          <Card hover>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-neutral-500">
              Symbol
            </p>
            <h3 className="mt-3 text-lg font-semibold text-white">
              The market
            </h3>
            <p className="mt-2 text-sm text-neutral-400">
              One of BTCUSDT, ETHUSDT, SOLUSDT or XAUUSD.
            </p>
          </Card>
          <Card hover>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-neutral-500">
              Timeframe
            </p>
            <h3 className="mt-3 text-lg font-semibold text-white">The window</h3>
            <p className="mt-2 text-sm text-neutral-400">
              One of 1m, 5m, 15m, 1h, 4h, 1d or 1w. Together they form the
              required Data Pair.
            </p>
          </Card>
        </div>
        <div className="mx-auto mt-8 max-w-4xl">
          <Card className="border-amber-500/20 bg-amber-500/[0.04]">
            <p className="text-sm text-amber-100/80">
              A request without a valid Data Pair is rejected before any agent
              runs. The sniper remains signal-only — no orders are ever placed.
            </p>
          </Card>
        </div>
      </section>

      {/* Agent teams */}
      <section className="mt-24">
        <SectionHeading
          eyebrow="The engine"
          title="Ten agents, four teams, one consensus"
          subtitle="Scores are combined with fixed team weights and normalized to a single directional signal."
        />
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {teams.map((team) => (
            <Card key={team.name} hover>
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white">{team.name}</h3>
                <Badge tone={team.tone}>{team.weight}</Badge>
              </div>
              <ul className="mt-4 space-y-2">
                {team.agents.map((agent) => (
                  <li
                    key={agent}
                    className="flex items-center gap-2 font-mono text-sm text-neutral-400"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-neutral-500" />
                    {agent}
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
        <div className="mt-8">
          <Card>
            <p className="text-sm text-neutral-400">
              The directional signal is the weighted consensus (technical 0.35 +
              market intel 0.25 + risk 0.20, normalized to /100). Confidence
              reflects how strongly and unanimously the agents agree.
            </p>
          </Card>
        </div>
      </section>

      <div className="mt-20 flex flex-wrap justify-center gap-3">
        <Button to="/dashboard" size="lg">
          Create your key
        </Button>
        <Button to="/docs" variant="secondary" size="lg">
          API reference
        </Button>
      </div>
    </div>
  );
}
