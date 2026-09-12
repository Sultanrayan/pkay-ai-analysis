import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, CodeBlock, cn } from "../components/ui.jsx";
import { MODELS } from "../lib/models.js";
import { AGENTS } from "../lib/agents.js";

const navGroups = [
  {
    label: "Getting started",
    items: [
      { id: "introduction", label: "Introduction" },
      { id: "quickstart", label: "Quickstart" },
      { id: "authentication", label: "Authentication" },
    ],
  },
  {
    label: "API reference",
    items: [
      { id: "endpoint", label: "Analyze endpoint" },
      { id: "agents", label: "Agents endpoint" },
      { id: "models", label: "Models" },
      { id: "request-json", label: "Request JSON" },
      { id: "data-pair", label: "Data Pair" },
      { id: "errors", label: "Errors" },
      { id: "rate-limits", label: "Rate limits" },
    ],
  },
];

const TIMEFRAMES = "1m · 5m · 15m · 1h · 4h · 1d · 1w";

const quickstart = `# 1. Create a key in the dashboard, then:
export PKAY_API_KEY="pk_live_xxxxxxxxxxxxxxxx"

# 2. Send a Data Pair to the analysis endpoint
curl -X POST https://api.pkay.ai/api/v3/analyze \\
  -H "Authorization: Bearer $PKAY_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{ "model": "deepseek-v4-flash", "symbol": "BTCUSDT", "timeframe": "15m" }'`;

const responseExample = `{
  "model": "deepseek-v4-flash",
  "symbol": "ETHUSDT",
  "timeframe": "4h",
  "signal": "BUY",
  "score": 58,
  "confidence": 82,
  "current_price": 3420.80,
  "agents": {
    "technical": 52.2, "volume": 41.0, "volatility": 28.5,
    "pattern": 47.1, "sentiment": 29.0, "onchain": 23.2,
    "macro": 17.4, "correlation": 12.0, "risk": 40.6, "sniper": 31.0
  },
  "risk": {
    "stop_loss": 3356.05, "take_profit": 3526.84, "position_size_pct": 2.5
  },
  "llm_enhanced": true,
  "summary": "Technical momentum is bullish, price is above the 50-period average...",
  "generated_at": "2026-09-11T14:30:00Z"
}`;

const jsExample = `import fetch from "node-fetch";

const res = await fetch("https://api.pkay.ai/api/v3/analyze", {
  method: "POST",
  headers: {
    Authorization: \`Bearer \${process.env.PKAY_API_KEY}\`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "kimi-k3",
    symbol: "SOLUSDT",
    timeframe: "15m",
    data: ["indicators", "sentiment", "risk"],
  }),
});

const analysis = await res.json();
console.log(analysis.signal, analysis.confidence);`;

const dataOptions = [
  ["indicators", "RSI, MACD, Bollinger, ATR, OBV and moving averages"],
  ["patterns", "Breakouts, chart patterns and support/resistance"],
  ["sentiment", "News scoring and the Fear & Greed index"],
  ["onchain", "Whale activity, exchange netflow and MVRV"],
  ["macro", "Rate policy, DXY and inflation backdrop"],
  ["correlation", "Cross-asset correlation (BTC↔XAU, ETH↔SOL)"],
  ["risk", "Stop-loss, take-profit and position sizing"],
  ["sniper", "Signal-only memecoin opportunity scan"],
];

const errors = [
  ["400", "Bad Request", "Missing or invalid Data Pair."],
  ["401", "Unauthorized", "API key missing, revoked or malformed."],
  ["403", "Forbidden", "Plan does not include this model or asset."],
  ["404", "Not Found", "Unknown model id."],
  ["429", "Too Many Requests", "Daily or monthly quota exceeded."],
  ["503", "Service Unavailable", "Upstream data source down; retry with backoff."],
];

export default function Docs() {
  const [active, setActive] = useState("introduction");
  const [activePayload, setActivePayload] = useState("full");
  const [selectedModel, setSelectedModel] = useState(
    () => MODELS.find((m) => m.default)?.id ?? MODELS[0].id
  );

  const payloads = [
    {
      key: "full",
      label: "Full analysis",
      json: `{
  "model": "${selectedModel}",
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "data": ["indicators", "patterns", "sentiment", "onchain", "macro", "correlation", "risk"]
}`,
    },
    {
      key: "technical",
      label: "Technical",
      json: `{
  "model": "${selectedModel}",
  "symbol": "ETHUSDT",
  "timeframe": "4h",
  "data": ["indicators", "patterns"]
}`,
    },
    {
      key: "intel",
      label: "Market intel",
      json: `{
  "model": "${selectedModel}",
  "symbol": "SOLUSDT",
  "timeframe": "1d",
  "data": ["sentiment", "onchain", "macro", "correlation"]
}`,
    },
    {
      key: "risk",
      label: "Risk",
      json: `{
  "model": "${selectedModel}",
  "symbol": "XAUUSD",
  "timeframe": "1h",
  "data": ["risk"]
}`,
    },
    {
      key: "sniper",
      label: "Sniper scan",
      json: `{
  "model": "${selectedModel}",
  "symbol": "SOLUSDT",
  "timeframe": "1h",
  "data": ["sniper"]
}`,
    },
    {
      key: "minimal",
      label: "Minimal",
      json: `{
  "symbol": "BTCUSDT",
  "timeframe": "1h"
}`,
    },
  ];

  const currentPayload =
    payloads.find((p) => p.key === activePayload) ?? payloads[0];

  const requestCurl = `curl -X POST https://api.pkay.ai/api/v3/analyze \\
  -H "Authorization: Bearer $PKAY_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '${currentPayload.json.replace(/\n/g, "\n  ")}'`;

  const serverResponse = `{
  "request_id": "req_9f2c41d8a6",
  "model": "${selectedModel}",
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "data": ["indicators", "sentiment", "risk"],
  "signal": "BUY",
  "score": 58,
  "confidence": 82,
  "current_price": 64120.50,
  "agents": {
    "technical": 52.2, "volume": 41.0, "volatility": 28.5,
    "pattern": 47.1, "sentiment": 29.0, "onchain": 23.2,
    "macro": 17.4, "correlation": 12.0, "risk": 40.6, "sniper": 31.0
  },
  "risk": {
    "stop_loss": 62900.0, "take_profit": 66100.0, "position_size_pct": 2.5
  },
  "llm_enhanced": true,
  "summary": "Technical momentum is bullish, price is above the 50-period average...",
  "generated_at": "2026-09-11T14:30:00Z"
}`;

  const agentsRequestJson = `{
  "functions": ["technical", "sentiment", "risk"],
  "format": "tools"
}`;

  const agentsCurl = `curl -X POST https://api.pkay.ai/api/v3/agents \\
  -H "Authorization: Bearer $PKAY_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '${agentsRequestJson.replace(/\n/g, "\n  ")}'`;

  const agentsResponse = `{
  "endpoint": "/api/v3/agents",
  "format": "tools",
  "count": 3,
  "functions": [
${AGENTS.slice(0, 3)
  .map(
    (a) =>
      `    {
      "name": "${a.fn}",
      "description": "${a.name} agent: ${a.description}",
      "parameters": {
        "type": "object",
        "properties": {
          "symbol": { "type": "string", "enum": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XAUUSD"] },
          "timeframe": { "type": "string", "enum": ["1m", "5m", "15m", "1h", "4h", "1d", "1w"] }
        },
        "required": ["symbol", "timeframe"]
      }
    }`
  )
  .join(",\n")}
  ]
}`;

  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mb-12">
        <p className="mb-5 text-sm font-semibold uppercase tracking-[0.2em] text-neutral-500">
          Documentation
        </p>
        <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
          Pkay AI <span className="text-gradient">Docs</span>
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-neutral-400">
          Two endpoints: analysis with built-in AI analysis, and the AI Agent
          Team functions for your own AI model.
        </p>
      </div>

      <div className="grid gap-10 lg:grid-cols-[240px_1fr]">
        {/* Sidebar */}
        <aside className="hidden lg:block">
          <nav className="sticky top-24 space-y-6">
            {navGroups.map((group) => (
              <div key={group.label}>
                <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-[0.18em] text-neutral-600">
                  {group.label}
                </p>
                <div className="space-y-1 border-l border-white/10">
                  {group.items.map((item) => (
                    <a
                      key={item.id}
                      href={`#${item.id}`}
                      onClick={() => setActive(item.id)}
                      className={cn(
                        "-ml-px block border-l-2 py-2 pl-3 text-sm transition",
                        active === item.id
                          ? "border-white text-white"
                          : "border-transparent text-neutral-500 hover:border-white/30 hover:text-white"
                      )}
                    >
                      {item.label}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        {/* Mobile nav */}
        <div className="-mt-2 flex gap-2 overflow-x-auto pb-2 lg:hidden">
          {navGroups.flatMap((group) => group.items).map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              onClick={() => setActive(item.id)}
              className={cn(
                "whitespace-nowrap rounded-full border px-3.5 py-1.5 text-sm transition",
                active === item.id
                  ? "border-white/40 bg-white/10 text-white"
                  : "border-white/10 text-neutral-500"
              )}
            >
              {item.label}
            </a>
          ))}
        </div>

        {/* Content */}
        <div className="min-w-0 space-y-16">
          <section id="introduction" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Introduction</h2>
            <p className="mt-3 leading-relaxed text-neutral-400">
              Pkay AI exposes two endpoints.{" "}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-neutral-200">
                POST /api/v3/analyze
              </code>{" "}
              runs the full multi-agent analysis and{" "}
              <strong className="text-neutral-200">
                comes with built-in AI analysis
              </strong>
              .{" "}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-neutral-200">
                POST /api/v3/agents
              </code>{" "}
              returns the AI Agent Team functions so you can call them from your
              own AI model. Every analysis request needs a Data Pair.
            </p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <Card>
                <p className="font-semibold text-white">Built-in AI analysis</p>
                <p className="mt-1 text-sm text-neutral-400">
                  <span className="font-mono text-neutral-300">
                    /api/v3/analyze
                  </span>{" "}
                  returns the full signal, scores and summary.
                </p>
              </Card>
              <Card>
                <p className="font-semibold text-white">
                  Functions for your AI
                </p>
                <p className="mt-1 text-sm text-neutral-400">
                  <span className="font-mono text-neutral-300">
                    /api/v3/agents
                  </span>{" "}
                  returns callable function definitions only.
                </p>
              </Card>
            </div>
          </section>

          <section id="quickstart" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Quickstart</h2>
            <p className="mt-3 leading-relaxed text-neutral-400">
              Generate a key in the{" "}
              <Link to="/dashboard" className="text-white hover:underline">
                dashboard
              </Link>{" "}
              and make your first call.
            </p>
            <CodeBlock code={quickstart} className="mt-5" />
          </section>

          <section id="authentication" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Authentication</h2>
            <p className="mt-3 leading-relaxed text-neutral-400">
              Pass your key as a bearer token. Keys are created and revoked in
              the dashboard and can be scoped per environment.
            </p>
            <CodeBlock
              code={`Authorization: Bearer pk_live_xxxxxxxxxxxxxxxx`}
              language="http"
              className="mt-5"
            />
            <Card className="mt-5 border-amber-500/20 bg-amber-500/[0.04]">
              <p className="text-sm text-amber-100/80">
                Never expose keys in client-side code. Keep them in server-side
                environment variables.
              </p>
            </Card>

            <h3 className="mt-8 font-semibold text-white">
              Sign in with Google
            </h3>
            <p className="mt-2 text-sm text-neutral-400">
              Accounts are created on first sign-in. The browser is redirected
              to Google and back to the callback, which returns a session token
              (send it as a Bearer token to <code className="font-mono">/api/v3/auth/me</code>).
            </p>
            <div className="mt-4 overflow-hidden rounded-xl border border-white/10">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/[0.03] text-neutral-400">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Method</th>
                    <th className="px-4 py-3 font-semibold">Endpoint</th>
                    <th className="px-4 py-3 font-semibold">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {[
                    [
                      "GET",
                      "/api/v3/auth/google",
                      "Redirect to Google sign-in / register",
                    ],
                    [
                      "GET",
                      "/api/v3/auth/google/callback",
                      "OAuth callback — exchanges the code, creates the account and issues a session token",
                    ],
                    [
                      "GET",
                      "/api/v3/auth/me",
                      "Return the signed-in account (Bearer session token)",
                    ],
                  ].map(([method, path, desc]) => (
                    <tr key={path}>
                      <td className="px-4 py-3 font-mono text-emerald-300">
                        {method}
                      </td>
                      <td className="px-4 py-3 font-mono text-neutral-200">
                        {path}
                      </td>
                      <td className="px-4 py-3 text-neutral-400">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <CodeBlock
              code={`https://auth.pkay.fun/api/v3/auth/google`}
              language="http"
              className="mt-3"
            />
          </section>

          {/* Analyze endpoint */}
          <section id="endpoint" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">
              Analyze endpoint
            </h2>
            <p className="mt-3 leading-relaxed text-neutral-400">
              Runs the multi-agent analysis for a Data Pair and returns the
              result with{" "}
              <strong className="text-neutral-200">
                built-in AI analysis
              </strong>{" "}
              — signal, score, confidence, agent scores and a summary.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Badge tone="green">POST</Badge>
              <code className="font-mono text-sm text-neutral-300">
                https://api.pkay.ai/api/v3/analyze
              </code>
            </div>

            <h3 className="mt-8 font-semibold text-white">Response</h3>
            <CodeBlock code={responseExample} language="json" className="mt-3" />

            <h3 className="mt-8 font-semibold text-white">JavaScript example</h3>
            <CodeBlock code={jsExample} language="javascript" className="mt-3" />
          </section>

          {/* Agents endpoint */}
          <section id="agents" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Agents endpoint</h2>
            <p className="mt-3 leading-relaxed text-neutral-400">
              The agents endpoint lets you request the callable functions for
              the AI Agent Team. It returns function definitions (tools) that an
              AI can call — nothing more. It does not run analysis, and you
              cannot attach or use your own AI model here.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Badge tone="green">POST</Badge>
              <code className="font-mono text-sm text-neutral-300">
                https://api.pkay.ai/api/v3/agents
              </code>
            </div>

            <Card className="mt-5 border-amber-500/20 bg-amber-500/[0.04]">
              <p className="text-sm text-amber-100/80">
                This endpoint only returns function definitions. It performs no
                analysis and does not accept or use your own AI model.
              </p>
            </Card>

            <h3 className="mt-8 font-semibold text-white">Request JSON</h3>
            <p className="mt-2 text-sm text-neutral-400">
              Send a JSON body to choose which functions to return and the
              output format. If omitted, all functions are returned.
            </p>
            <CodeBlock
              code={agentsRequestJson}
              language="json"
              className="mt-3"
            />
            <div className="mt-5 overflow-hidden rounded-xl border border-white/10">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/[0.03] text-neutral-400">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Field</th>
                    <th className="px-4 py-3 font-semibold">Type</th>
                    <th className="px-4 py-3 font-semibold">Required</th>
                    <th className="px-4 py-3 font-semibold">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  <tr>
                    <td className="px-4 py-3 font-mono text-neutral-200">
                      functions
                    </td>
                    <td className="px-4 py-3 text-neutral-400">string[]</td>
                    <td className="px-4 py-3 text-neutral-500">no</td>
                    <td className="px-4 py-3 text-neutral-400">
                      Function ids to return. Defaults to all.
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-mono text-neutral-200">
                      format
                    </td>
                    <td className="px-4 py-3 text-neutral-400">string</td>
                    <td className="px-4 py-3 text-neutral-500">no</td>
                    <td className="px-4 py-3 text-neutral-400">
                      tools (default) or json.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 className="mt-8 font-semibold text-white">Full request</h3>
            <CodeBlock code={agentsCurl} className="mt-3" />

            <h3 className="mt-8 font-semibold text-white">Functions</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {AGENTS.map((agent) => (
                <div
                  key={agent.id}
                  className="rounded-xl border border-white/10 bg-white/[0.02] p-4"
                >
                  <code className="font-mono text-sm text-neutral-200">
                    {agent.fn}
                  </code>
                  <p className="mt-1 text-xs text-neutral-500">
                    {agent.team} · weight {agent.weight}
                  </p>
                  <p className="mt-2 text-sm text-neutral-400">
                    {agent.description}
                  </p>
                </div>
              ))}
            </div>

            <h3 className="mt-8 font-semibold text-white">Response</h3>
            <CodeBlock code={agentsResponse} language="json" className="mt-3" />
          </section>

          {/* Models */}
          <section id="models" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Models</h2>
            <p className="mt-3 leading-relaxed text-neutral-400">
              Choose the AI Model that powers your analysis. Pass its id in the{" "}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-neutral-200">
                model
              </code>{" "}
              field of{" "}
              <span className="font-mono text-neutral-300">
                /api/v3/analyze
              </span>
              . If omitted, the default is{" "}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-neutral-200">
                deepseek-v4-flash
              </code>
              .
            </p>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {MODELS.map((model) => {
                const selected = selectedModel === model.id;
                return (
                  <button
                    key={model.id}
                    type="button"
                    onClick={() => setSelectedModel(model.id)}
                    className={cn(
                      "group flex items-start gap-4 rounded-2xl border p-4 text-left transition",
                      selected
                        ? "border-white/40 bg-white/[0.06]"
                        : "border-white/10 bg-white/[0.02] hover:border-white/25 hover:bg-white/[0.04]"
                    )}
                  >
                    <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white">
                      <img
                        src={model.logo}
                        alt={`${model.name} logo`}
                        className="h-6 w-6"
                        loading="lazy"
                      />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-white">
                          {model.name}
                        </span>
                        {selected && (
                          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                            Selected
                          </span>
                        )}
                      </span>
                      <span className="mt-0.5 block text-xs text-neutral-500">
                        {model.vendor}
                      </span>
                      <code className="mt-2 inline-block rounded-md border border-white/10 bg-black/40 px-2 py-0.5 font-mono text-xs text-neutral-200">
                        {model.id}
                      </code>
                      <span className="mt-2 block text-sm leading-relaxed text-neutral-400">
                        {model.description}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          {/* Request JSON */}
          <section id="request-json" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Request JSON</h2>
            <p className="mt-3 leading-relaxed text-neutral-400">
              The body for{" "}
              <span className="font-mono text-neutral-300">
                /api/v3/analyze
              </span>{" "}
              tells Pkay AI which model to use and which data you want analysed.
              Only{" "}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-neutral-200">
                symbol
              </code>{" "}
              and{" "}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-neutral-200">
                timeframe
              </code>{" "}
              are required; everything else is optional.
            </p>

            <div className="mt-5 overflow-hidden rounded-xl border border-white/10">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/[0.03] text-neutral-400">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Field</th>
                    <th className="px-4 py-3 font-semibold">Type</th>
                    <th className="px-4 py-3 font-semibold">Required</th>
                    <th className="px-4 py-3 font-semibold">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  <tr>
                    <td className="px-4 py-3 font-mono text-neutral-200">
                      model
                    </td>
                    <td className="px-4 py-3 text-neutral-400">string</td>
                    <td className="px-4 py-3 text-neutral-500">no</td>
                    <td className="px-4 py-3 text-neutral-400">
                      Model id. Defaults to deepseek-v4-flash.
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-mono text-neutral-200">
                      symbol
                    </td>
                    <td className="px-4 py-3 text-neutral-400">string</td>
                    <td className="px-4 py-3 text-emerald-300">yes</td>
                    <td className="px-4 py-3 text-neutral-400">
                      BTCUSDT · ETHUSDT · SOLUSDT · XAUUSD
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-mono text-neutral-200">
                      timeframe
                    </td>
                    <td className="px-4 py-3 text-neutral-400">string</td>
                    <td className="px-4 py-3 text-emerald-300">yes</td>
                    <td className="px-4 py-3 text-neutral-400">
                      {TIMEFRAMES}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-mono text-neutral-200">
                      data
                    </td>
                    <td className="px-4 py-3 text-neutral-400">string[]</td>
                    <td className="px-4 py-3 text-neutral-500">no</td>
                    <td className="px-4 py-3 text-neutral-400">
                      The datasets to analyse. Defaults to all.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 className="mt-8 font-semibold text-white">Available data</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {dataOptions.map(([key, desc]) => (
                <div
                  key={key}
                  className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-3"
                >
                  <code className="rounded-md border border-white/10 bg-black/40 px-2 py-0.5 font-mono text-xs text-neutral-200">
                    {key}
                  </code>
                  <span className="text-sm text-neutral-400">{desc}</span>
                </div>
              ))}
            </div>

            <h3 className="mt-8 font-semibold text-white">Ready-to-send JSON</h3>
            <p className="mt-2 text-sm text-neutral-400">
              Copy a payload and POST it to our server. The tabs show common
              data selections — the active model is included automatically.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {payloads.map((payload) => (
                <button
                  key={payload.key}
                  type="button"
                  onClick={() => setActivePayload(payload.key)}
                  className={cn(
                    "rounded-lg border px-3 py-1.5 text-xs font-medium transition",
                    activePayload === payload.key
                      ? "border-white/40 bg-white/10 text-white"
                      : "border-white/10 text-neutral-400 hover:border-white/25 hover:text-white"
                  )}
                >
                  {payload.label}
                </button>
              ))}
            </div>
            <CodeBlock
              code={currentPayload.json}
              language="json"
              className="mt-3"
            />

            <h3 className="mt-8 font-semibold text-white">Full request</h3>
            <CodeBlock code={requestCurl} className="mt-3" />

            <h3 className="mt-8 font-semibold text-white">Server response</h3>
            <p className="mt-2 text-sm text-neutral-400">
              The JSON our server returns for a successful analysis request.
            </p>
            <CodeBlock code={serverResponse} language="json" className="mt-3" />
          </section>

          <section id="data-pair" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Data Pair</h2>
            <p className="mt-3 leading-relaxed text-neutral-400">
              A Data Pair is the combination of{" "}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-neutral-200">
                symbol
              </code>{" "}
              and{" "}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-neutral-200">
                timeframe
              </code>
              . It tells the AI Agent Team exactly what to analyse. A request
              without a valid Data Pair is rejected before any agent runs.
            </p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <Card>
                <p className="font-mono text-sm text-neutral-200">
                  BTCUSDT + 15m
                </p>
                <p className="mt-2 text-sm text-neutral-400">Valid Data Pair</p>
              </Card>
              <Card className="border-rose-500/20">
                <p className="font-mono text-sm text-rose-300">
                  timeframe only
                </p>
                <p className="mt-2 text-sm text-neutral-400">
                  Invalid — 400 error
                </p>
              </Card>
            </div>
          </section>

          <section id="errors" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Errors</h2>
            <div className="mt-5 overflow-hidden rounded-xl border border-white/10">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/[0.03] text-neutral-400">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Status</th>
                    <th className="px-4 py-3 font-semibold">Name</th>
                    <th className="px-4 py-3 font-semibold">Cause</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {errors.map(([status, name, cause]) => (
                    <tr key={status}>
                      <td className="px-4 py-3 font-mono text-amber-300">
                        {status}
                      </td>
                      <td className="px-4 py-3 text-neutral-300">{name}</td>
                      <td className="px-4 py-3 text-neutral-400">{cause}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section id="rate-limits" className="scroll-mt-24">
            <h2 className="text-2xl font-bold text-white">Rate limits</h2>
            <ul className="mt-4 space-y-3 text-neutral-400">
              <li className="flex gap-2">
                <span className="text-neutral-500">•</span> Free: 100 requests
                per month.
              </li>
              <li className="flex gap-2">
                <span className="text-neutral-500">•</span> Developer: 5,000
                requests per month.
              </li>
              <li className="flex gap-2">
                <span className="text-neutral-500">•</span> Start Up: 25,000
                requests per month with a priority queue.
              </li>
              <li className="flex gap-2">
                <span className="text-neutral-500">•</span> Exceeding a limit
                returns{" "}
                <code className="font-mono text-sm text-amber-300">429</code>.
              </li>
            </ul>
          </section>

          <div className="flex flex-wrap gap-3 border-t border-white/10 pt-10">
            <Button to="/dashboard">Create an API key</Button>
            <Button to="/pricing" variant="secondary">
              View pricing
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
