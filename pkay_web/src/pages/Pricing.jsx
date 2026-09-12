import { useState } from "react";
import {
  Badge,
  Button,
  Card,
  SectionHeading,
  cn,
} from "../components/ui.jsx";
import { Reveal, SpotlightCard } from "../components/premium.jsx";

const plans = [
  {
    name: "Free",
    monthly: 0,
    yearly: 0,
    tagline: "Explore the analysis API.",
    cta: "Start free",
    features: [
      {
        name: "100 requests / month",
        description: "Enough to explore the endpoint",
        included: true,
      },
      {
        name: "DeepSeek V4 Flash",
        description: "Default analysis model",
        included: true,
      },
      {
        name: "All 10 agents",
        description: "Full multi-agent consensus",
        included: true,
      },
      {
        name: "Deterministic analysis",
        description: "Rule-based signals",
        included: true,
      },
      {
        name: "Premium models",
        description: "V4 Pro, GLM 5.3 and more",
        included: false,
      },
    ],
  },
  {
    name: "Developer",
    monthly: 29,
    yearly: 290,
    tagline: "For builders shipping analysis.",
    cta: "Choose Developer",
    highlight: true,
    badge: "Most popular",
    features: [
      {
        name: "5,000 requests / month",
        description: "Comfortable for side projects",
        included: true,
      },
      {
        name: "DeepSeek V4 Flash · V4 Pro · GLM 5.3",
        description: "Three analysis models",
        included: true,
      },
      {
        name: "All assets + sniper",
        description: "BTC, ETH, SOL, XAU and memecoins",
        included: true,
      },
      {
        name: "Usage analytics",
        description: "Requests, errors and per-asset volume",
        included: true,
      },
      {
        name: "Priority support",
        description: "Dedicated support channel",
        included: false,
      },
    ],
  },
  {
    name: "Start Up",
    monthly: 99,
    yearly: 990,
    tagline: "For teams scaling production traffic.",
    cta: "Choose Start Up",
    features: [
      {
        name: "25,000 requests / month",
        description: "Room to grow without limits",
        included: true,
      },
      {
        name: "All AI models",
        description: "Claude, GPT, GLM, DeepSeek and Kimi",
        included: true,
      },
      {
        name: "Unlimited API keys",
        description: "Scope keys per service and environment",
        included: true,
      },
      {
        name: "Priority queue",
        description: "Lower latency under load",
        included: true,
      },
      {
        name: "Priority support",
        description: "Dedicated support channel",
        included: true,
      },
    ],
  },
  {
    name: "Enterprise",
    monthly: 299,
    yearly: 2990,
    tagline: "For mission-critical deployments.",
    cta: "Contact sales",
    features: [
      {
        name: "Custom requests",
        description: "Volume pricing beyond 25,000 / month",
        included: true,
      },
      {
        name: "Custom models",
        description: "Fine-tuning and private routing",
        included: true,
      },
      {
        name: "99.99% uptime SLA",
        description: "Contractual guarantees",
        included: true,
      },
      {
        name: "SSO, audit logs & RBAC",
        description: "Enterprise-grade security",
        included: true,
      },
      {
        name: "Dedicated infrastructure",
        description: "Isolated capacity and onboarding",
        included: true,
      },
    ],
  },
];

const comparison = [
  ["Requests", "100 / mo", "5,000 / mo", "25,000 / mo", "Custom"],
  [
    "Models",
    "DeepSeek V4 Flash",
    "Flash · V4 Pro · GLM 5.3",
    "All models",
    "Custom",
  ],
  ["Assets", "4", "4 + sniper", "4 + sniper", "4 + sniper"],
  ["API keys", "1", "5", "Unlimited", "Unlimited"],
  ["Usage analytics", false, true, true, true],
  ["Priority queue", false, false, true, true],
  ["SSO & audit logs", false, false, false, true],
  ["Support", "Community", "Email", "Priority", "Dedicated"],
];

const agentsEndpoint = {
  endpoint: "/api/v3/agents",
  method: "POST",
  title: "AI Agent Team functions",
  subtitle:
    "Callable function definitions for the AI to use. Functions-only — no analysis, no model.",
};

const agentPlans = [
  {
    name: "Free",
    monthly: 0,
    yearly: 0,
    tagline: "Explore the function catalogue.",
    cta: "Start free",
    features: [
      {
        name: "1,000 requests / month",
        description: "Enough to explore the endpoint",
        included: true,
      },
      {
        name: "analyze_technical · analyze_volume",
        description: "Two functions",
        included: true,
      },
      {
        name: "Function definitions only",
        description: "No analysis, no model",
        included: true,
      },
      {
        name: "All functions",
        description: "analyze_* and scan_sniper",
        included: false,
      },
    ],
  },
  {
    name: "Developer",
    monthly: 15,
    yearly: 150,
    tagline: "For builders wiring functions into their AI.",
    cta: "Choose Developer",
    highlight: true,
    badge: "Most popular",
    features: [
      {
        name: "20,000 requests / month",
        description: "Comfortable for side projects",
        included: true,
      },
      {
        name: "All functions",
        description: "analyze_* and scan_sniper",
        included: true,
      },
      {
        name: "Function definitions only",
        description: "No analysis, no model",
        included: true,
      },
      {
        name: "Priority support",
        description: "Dedicated support channel",
        included: false,
      },
    ],
  },
  {
    name: "Start Up",
    monthly: 79,
    yearly: 790,
    tagline: "For teams scaling production traffic.",
    cta: "Choose Start Up",
    features: [
      {
        name: "150,000 requests / month",
        description: "Room to grow without limits",
        included: true,
      },
      {
        name: "All functions",
        description: "analyze_* and scan_sniper",
        included: true,
      },
      {
        name: "Unlimited API keys",
        description: "Scope keys per service and environment",
        included: true,
      },
      {
        name: "Priority queue",
        description: "Lower latency under load",
        included: true,
      },
      {
        name: "Priority support",
        description: "Dedicated support channel",
        included: true,
      },
    ],
  },
  {
    name: "Enterprise",
    monthly: 300,
    yearly: 3000,
    tagline: "For mission-critical deployments.",
    cta: "Contact sales",
    features: [
      {
        name: "Custom requests",
        description: "Volume pricing beyond 150,000 / month",
        included: true,
      },
      {
        name: "All functions",
        description: "analyze_* and scan_sniper",
        included: true,
      },
      {
        name: "99.99% uptime SLA",
        description: "Contractual guarantees",
        included: true,
      },
      {
        name: "SSO, audit logs & RBAC",
        description: "Enterprise-grade security",
        included: true,
      },
      {
        name: "Dedicated infrastructure",
        description: "Isolated capacity and onboarding",
        included: true,
      },
    ],
  },
];

const faqs = [
  {
    q: "Do I need a Data Connect?",
    a: "No. Pkay AI removed Data Connect. You call one endpoint, POST /api/v3/analyze, and pass a Data Pair.",
  },
  {
    q: "What exactly is a Data Pair?",
    a: "The symbol and timeframe for the analysis, for example BTCUSDT + 1h. Every request must include a valid Data Pair.",
  },
  {
    q: "Can I switch between models?",
    a: "Yes. Pass the model id in the request body. Free uses the default; Developer and above unlock the latest AI Model and the full model catalogue.",
  },
  {
    q: "Can I change plans later?",
    a: "Yes. Upgrades take effect immediately and downgrades at the end of the current billing period.",
  },
  {
    q: "Does the sniper place trades?",
    a: "Never. The sniper is signal-only and every opportunity ships with a safety profile and disclaimer.",
  },
];

function PriceValue({ plan, yearly }) {
  if (plan.custom) {
    return <span className="text-4xl font-extrabold text-white">Custom</span>;
  }
  const amount = yearly ? plan.yearly : plan.monthly;
  return (
    <span className="flex items-end gap-1">
      <span className="text-4xl font-extrabold text-white">${amount}</span>
      <span className="pb-1 text-sm text-neutral-500">
        /{yearly ? "year" : "month"}
      </span>
    </span>
  );
}

function PlanCard({ plan, yearly }) {
  return (
    <SpotlightCard
      className={cn(
        "flex h-full flex-col p-6",
        plan.highlight &&
          "border-white/30 bg-white/[0.05] shadow-[0_30px_80px_-40px_rgba(255,255,255,0.35)]"
      )}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
        {plan.badge && <Badge tone="brand">{plan.badge}</Badge>}
      </div>
      <p className="mt-1 text-sm text-neutral-400">{plan.tagline}</p>

      <div className="mt-6">
        <PriceValue plan={plan} yearly={yearly} />
      </div>

      <Button
        to={plan.name === "Enterprise" ? "/about#contact" : "/dashboard"}
        variant={plan.highlight ? "primary" : "secondary"}
        className="mt-6 w-full"
      >
        {plan.cta}
      </Button>

      <ul className="mt-6 space-y-4">
        {plan.features.map((feature) => (
          <li key={feature.name} className="flex items-start gap-3">
            <span
              className={cn(
                "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full",
                feature.included ? "bg-emerald-400" : "bg-neutral-700"
              )}
            />
            <span>
              <span
                className={cn(
                  "block text-sm font-medium",
                  feature.included ? "text-neutral-200" : "text-neutral-500"
                )}
              >
                {feature.name}
              </span>
              <span className="block text-xs text-neutral-500">
                {feature.description}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </SpotlightCard>
  );
}

export default function Pricing() {
  const [yearly, setYearly] = useState(false);
  const [open, setOpen] = useState(0);

  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <SectionHeading
        eyebrow="Pricing"
        title="Plans for every stage"
        subtitle="Pricing for the analysis endpoint. Start free and scale to production."
      />

      <div className="mt-6 flex justify-center">
        <span className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2">
          <Badge tone="green">POST</Badge>
          <code className="font-mono text-sm text-neutral-200">
            /api/v3/analyze
          </code>
        </span>
      </div>

      <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
        <span
          className={cn(
            "text-sm",
            !yearly ? "text-white" : "text-neutral-500"
          )}
        >
          Monthly
        </span>
        <button
          onClick={() => setYearly((v) => !v)}
          className={cn(
            "relative h-7 w-14 rounded-full border transition",
            yearly
              ? "border-white/40 bg-white/20"
              : "border-white/15 bg-white/10"
          )}
          aria-label="Toggle billing period"
        >
          <span
            className={cn(
              "absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all",
              yearly ? "left-8" : "left-0.5"
            )}
          />
        </button>
        <span
          className={cn("text-sm", yearly ? "text-white" : "text-neutral-500")}
        >
          Yearly
        </span>
        <Badge tone="green">Save 2 months</Badge>
      </div>

      <div className="mt-14 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        {plans.map((plan, index) => (
          <Reveal key={plan.name} delay={index * 80}>
            <PlanCard plan={plan} yearly={yearly} />
          </Reveal>
        ))}
      </div>

      {/* Agents endpoint pricing */}
      <section className="mt-24">
        <SectionHeading
          eyebrow="Endpoint pricing"
          title={agentsEndpoint.title}
          subtitle={agentsEndpoint.subtitle}
        />
        <div className="mt-6 flex justify-center">
          <span className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2">
            <Badge tone="green">{agentsEndpoint.method}</Badge>
            <code className="font-mono text-sm text-neutral-200">
              {agentsEndpoint.endpoint}
            </code>
          </span>
        </div>
        <div className="mt-14 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {agentPlans.map((plan, index) => (
            <Reveal key={plan.name} delay={index * 80}>
              <PlanCard plan={plan} yearly={yearly} />
            </Reveal>
          ))}
        </div>
      </section>

      {/* Comparison table */}
      <section className="mt-24">
        <SectionHeading
          eyebrow="Compare"
          title="Every plan, side by side"
          subtitle="A closer look at limits, models and support across tiers."
        />
        <Card className="mt-12 overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 bg-white/[0.03]">
                  <th className="px-6 py-4 font-semibold text-neutral-400">
                    Feature
                  </th>
                  {plans.map((plan) => (
                    <th
                      key={plan.name}
                      className={cn(
                        "px-6 py-4 text-center font-semibold",
                        plan.highlight ? "text-white" : "text-neutral-300"
                      )}
                    >
                      {plan.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {comparison.map(([label, free, dev, startup, ent]) => (
                  <tr key={label}>
                    <td className="px-6 py-4 text-neutral-400">{label}</td>
                    {[free, dev, startup, ent].map((value, i) => (
                      <td key={i} className="px-6 py-4 text-center">
                        {typeof value === "boolean" ? (
                          <span
                            className={cn(
                              "text-sm",
                              value ? "text-emerald-300" : "text-neutral-600"
                            )}
                          >
                            {value ? "Yes" : "—"}
                          </span>
                        ) : (
                          <span className="text-neutral-300">{value}</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </section>

      {/* FAQ */}
      <section className="mt-24">
        <SectionHeading eyebrow="FAQ" title="Questions, answered" />
        <div className="mx-auto mt-12 max-w-3xl space-y-3">
          {faqs.map((faq, index) => (
            <Card key={faq.q} className="p-0">
              <button
                onClick={() => setOpen(open === index ? -1 : index)}
                className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
              >
                <span className="font-medium text-white">{faq.q}</span>
                <span className="text-lg text-neutral-400">
                  {open === index ? "−" : "+"}
                </span>
              </button>
              {open === index && (
                <p className="px-6 pb-5 text-sm leading-relaxed text-neutral-400">
                  {faq.a}
                </p>
              )}
            </Card>
          ))}
        </div>
      </section>

      <div className="mt-16 flex justify-center">
        <Button to="/dashboard" size="lg">
          Create an API key
        </Button>
      </div>
    </div>
  );
}
