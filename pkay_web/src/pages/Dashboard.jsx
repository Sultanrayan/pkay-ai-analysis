import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Badge,
  Button,
  Card,
  CodeBlock,
  StatCard,
  cn,
} from "../components/ui.jsx";
import { SymbolBarChart, UsageAreaChart } from "../components/charts.jsx";
import DashboardSidebar from "../components/dashboard-sidebar.jsx";
import AdvancedStats from "../components/advanced-stats.jsx";
import Settings from "../components/settings.jsx";
import {
  ActivityFeed,
  ModelUsageCard,
  QuickStartCard,
} from "../components/dashboard-widgets.jsx";
import { api, authUrl } from "../lib/api.js";
import { applyTheme, loadTheme, resolveTheme } from "../lib/theme.js";

const SCOPES = [
  { id: "analyze", label: "Analysis" },
  { id: "agents", label: "Functions" },
  { id: "sniper", label: "Sniper" },
];

const EMPTY_USAGE = {
  summary: { total: 0, today: 0, errors: 0, success_rate: 100 },
  series: [],
  by_model: [],
  by_endpoint: [],
  by_symbol: [],
  recent: [],
};

const SECTION_TITLES = {
  overview: "Overview",
  keys: "API Keys",
  usage: "Usage",
  playground: "Playground",
};

function timeAgo(iso) {
  if (!iso) return "";
  const diff = Math.max(0, Date.now() - new Date(iso).getTime());
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} h ago`;
  return `${Math.floor(hours / 24)} d ago`;
}

function CopyButton({ value, className }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        } catch {
          /* ignore */
        }
      }}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-neutral-300 transition hover:text-white",
        className
      )}
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function KeyCreator({ onCreated, onError }) {
  const [name, setName] = useState("");
  const [environment, setEnvironment] = useState("live");
  const [scopes, setScopes] = useState(["analyze"]);
  const [busy, setBusy] = useState(false);

  const toggleScope = (id) =>
    setScopes((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const key = await api.createKey({ name, environment, scopes });
      onCreated(key);
      setName("");
      setScopes(["analyze"]);
      setEnvironment("live");
    } catch (err) {
      onError?.(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold text-white">Create a new API key</h3>
      <form onSubmit={submit} className="mt-5 space-y-5">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-neutral-300">
            Key name
          </label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. production-bot"
            className="w-full rounded-xl border border-white/10 bg-ink-900/70 px-4 py-2.5 text-sm text-white placeholder:text-neutral-600 focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/10"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-neutral-300">
            Environment
          </label>
          <div className="flex gap-2">
            {["live", "test"].map((env) => (
              <button
                key={env}
                type="button"
                onClick={() => setEnvironment(env)}
                className={cn(
                  "flex-1 rounded-xl border px-4 py-2.5 text-sm font-medium capitalize transition",
                  environment === env
                    ? "border-white/40 bg-white/10 text-white"
                    : "border-white/10 bg-white/[0.02] text-neutral-400 hover:text-white"
                )}
              >
                {env}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-neutral-300">
            Scopes
          </label>
          <div className="flex flex-wrap gap-2">
            {SCOPES.map((scope) => (
              <button
                key={scope.id}
                type="button"
                onClick={() => toggleScope(scope.id)}
                className={cn(
                  "rounded-lg border px-3 py-2 text-sm transition",
                  scopes.includes(scope.id)
                    ? "border-white/40 bg-white/10 text-white"
                    : "border-white/10 bg-white/[0.02] text-neutral-400 hover:text-white"
                )}
              >
                {scope.label}
              </button>
            ))}
          </div>
        </div>

        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Generating…" : "Generate key"}
        </Button>
      </form>
    </Card>
  );
}

function NewKeyBanner({ apiKey, onDismiss }) {
  if (!apiKey) return null;
  return (
    <Card className="border-emerald-500/30 bg-emerald-500/[0.06]">
      <p className="font-semibold text-white">
        Your new key "{apiKey.name}" is ready
      </p>
      <p className="mt-1 text-sm text-emerald-100/70">
        Copy it now — for security you will not be able to see it again in full.
      </p>
      <div className="mt-3 flex items-center gap-2 rounded-xl border border-white/10 bg-black/70 px-3 py-2">
        <code className="min-w-0 flex-1 truncate font-mono text-sm text-emerald-300">
          {apiKey.secret}
        </code>
        <CopyButton value={apiKey.secret} />
      </div>
      <Button variant="ghost" size="sm" className="mt-3" onClick={onDismiss}>
        Dismiss
      </Button>
    </Card>
  );
}

function KeyRow({ apiKey, onRevoke, onDelete }) {
  const revoked = apiKey.status === "revoked";
  return (
    <div className="flex flex-col gap-4 border-b border-white/5 px-5 py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium text-white">{apiKey.name}</p>
          <Badge tone={apiKey.environment === "live" ? "green" : "slate"}>
            {apiKey.environment}
          </Badge>
          {revoked ? (
            <Badge tone="amber">revoked</Badge>
          ) : (
            <Badge tone="brand">active</Badge>
          )}
        </div>
        <p className="mt-1.5 truncate font-mono text-sm text-neutral-500">
          {revoked ? "pk_••••••••••••••••" : `${apiKey.key_prefix}••••••••••••`}
        </p>
        <p className="mt-1 text-xs text-neutral-600">
          Created {new Date(apiKey.created_at).toLocaleDateString()} · Scopes:{" "}
          {apiKey.scopes.length ? apiKey.scopes.join(", ") : "none"} ·{" "}
          {apiKey.request_count} requests
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {!revoked ? (
          <Button variant="danger" size="sm" onClick={() => onRevoke(apiKey.id)}>
            Revoke
          </Button>
        ) : (
          <Button variant="ghost" size="sm" onClick={() => onDelete(apiKey.id)}>
            Delete
          </Button>
        )}
      </div>
    </div>
  );
}

function Playground() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("15m");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const run = async () => {
    setLoading(true);
    setResult(null);
    setError("");
    try {
      const data = await api.analyze({
        symbol,
        timeframe,
        data: ["indicators", "risk", "sentiment"],
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <h3 className="text-lg font-semibold text-white">Request builder</h3>
        <p className="mt-1 text-sm text-neutral-400">
          Send a Data Pair to <code className="font-mono">/api/v3/analyze</code>.
        </p>

        <div className="mt-5 space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-neutral-300">
              Symbol
            </label>
            <div className="grid grid-cols-2 gap-2">
              {["BTCUSDT", "ETHUSDT", "SOLUSDT", "XAUUSD"].map((s) => (
                <button
                  key={s}
                  onClick={() => setSymbol(s)}
                  className={cn(
                    "rounded-xl border px-3 py-2.5 text-sm font-medium transition",
                    symbol === s
                      ? "border-white/40 bg-white/10 text-white"
                      : "border-white/10 bg-white/[0.02] text-neutral-400 hover:text-white"
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-neutral-300">
              Timeframe
            </label>
            <div className="grid grid-cols-4 gap-2">
              {["1m", "5m", "15m", "1h", "4h", "1d", "1w"].map((t) => (
                <button
                  key={t}
                  onClick={() => setTimeframe(t)}
                  className={cn(
                    "rounded-xl border px-3 py-2.5 text-sm font-medium transition",
                    timeframe === t
                      ? "border-white/40 bg-white/10 text-white"
                      : "border-white/10 bg-white/[0.02] text-neutral-400 hover:text-white"
                  )}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <Button onClick={run} disabled={loading} className="w-full">
            {loading ? "Running agents…" : "Send request"}
          </Button>
        </div>
      </Card>

      <Card className="flex flex-col">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Response</h3>
          {result && <Badge tone="green">200 OK</Badge>}
          {error && <Badge tone="amber">Error</Badge>}
        </div>
        {error ? (
          <div className="mt-4 rounded-xl border border-rose-500/20 bg-rose-500/[0.05] p-4 text-sm text-rose-300">
            {error}
          </div>
        ) : result ? (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                <p className="text-xs text-neutral-500">Signal</p>
                <p
                  className={cn(
                    "text-lg font-bold",
                    result.signal === "BUY"
                      ? "text-emerald-400"
                      : result.signal === "SELL"
                        ? "text-rose-400"
                        : "text-amber-300"
                  )}
                >
                  {result.signal}
                </p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                <p className="text-xs text-neutral-500">Confidence</p>
                <p className="text-lg font-bold text-white">
                  {result.confidence}%
                </p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                <p className="text-xs text-neutral-500">Score</p>
                <p className="text-lg font-bold text-neutral-200">
                  {result.score > 0 ? `+${result.score}` : result.score}
                </p>
              </div>
            </div>
            <CodeBlock
              code={JSON.stringify(result, null, 2)}
              language="json"
            />
          </div>
        ) : (
          <div className="mt-4 flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-white/10 py-16 text-center">
            <p className="text-sm text-neutral-500">
              Run a request to see the AI Model output.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}

function SignedOut() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-black p-4">
      <Card className="w-full max-w-sm text-center">
        <p className="text-lg font-semibold text-white">Dashboard</p>
        <p className="mt-2 text-sm text-neutral-400">
          Sign in with Google to view your keys and usage.
        </p>
        <Button href={authUrl} className="mt-6 w-full">
          Continue with Google
        </Button>
      </Card>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [signedIn, setSignedIn] = useState(() => api.isSignedIn());
  const [user, setUser] = useState(null);
  const [keys, setKeys] = useState([]);
  const [usage, setUsage] = useState(EMPTY_USAGE);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [section, setSection] = useState("overview");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [theme, setTheme] = useState(() => loadTheme());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [newKey, setNewKey] = useState(null);

  const refresh = useCallback(async () => {
    const [me, keysResponse, usageResponse] = await Promise.all([
      api.me(),
      api.listKeys(),
      api.usage(14),
    ]);
    setUser(me);
    setKeys(keysResponse.keys || []);
    setUsage({ ...EMPTY_USAGE, ...usageResponse });
    setLoaded(true);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      api.setToken(token);
      setSignedIn(true);
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    if (!signedIn) return;
    let active = true;
    refresh().catch((err) => {
      if (!active) return;
      if (err.status === 401) {
        api.clearToken();
        setSignedIn(false);
      } else {
        setError(err.message);
      }
    });
    return () => {
      active = false;
    };
  }, [signedIn, refresh]);

  const summary = useMemo(() => {
    const series = usage.series;
    const today = series[series.length - 1]?.requests ?? 0;
    const prev = series[series.length - 2]?.requests ?? 0;
    const change = prev ? Math.round(((today - prev) / prev) * 100) : 0;
    return {
      total: usage.summary.total,
      today: usage.summary.today,
      errors: usage.summary.errors,
      successRate: usage.summary.success_rate,
      change,
    };
  }, [usage]);

  const modelUsage = useMemo(
    () =>
      usage.by_model.map((item) => ({
        name: item.label,
        pct: usage.summary.total
          ? Math.round((item.count / usage.summary.total) * 100)
          : 0,
      })),
    [usage]
  );

  const activity = useMemo(
    () =>
      usage.recent.map((row) => ({
        title: `${row.endpoint} · ${row.symbol || "—"} ${row.timeframe || ""}`,
        time: `${row.status_code} · ${timeAgo(row.created_at)}`,
      })),
    [usage]
  );

  const breakdown = useMemo(
    () =>
      usage.by_symbol.map((item) => ({
        symbol: item.label,
        requests: item.count,
      })),
    [usage]
  );

  const activeKeys = keys.filter((key) => key.status === "active").length;

  const navGroups = [
    {
      items: [
        { id: "overview", title: "Overview" },
        { id: "keys", title: "API Keys", badge: activeKeys },
      ],
    },
    {
      heading: "Workspace",
      items: [
        {
          id: "usage",
          title: "Usage",
          children: [
            { id: "usage-requests", title: "Requests" },
            { id: "usage-assets", title: "By asset" },
          ],
        },
        { id: "playground", title: "Playground" },
      ],
    },
  ];

  const bottomItems = [
    { id: "profile", title: "Profile" },
    { id: "docs", title: "Documentation", shortcut: "⌘/" },
  ];

  const handleSelect = (id) => {
    if (id === "profile") {
      setSettingsOpen(true);
      setMobileOpen(false);
      return;
    }
    if (id === "docs") {
      navigate("/docs");
      return;
    }
    if (id.startsWith("usage")) {
      setSection("usage");
      setMobileOpen(false);
      return;
    }
    setSection(id);
    setMobileOpen(false);
  };

  const handleCreated = async (key) => {
    setNewKey(key);
    try {
      const response = await api.listKeys();
      setKeys(response.keys || []);
    } catch (err) {
      setError(err.message);
    }
    setSection("keys");
  };

  const handleRevoke = async (id) => {
    try {
      await api.revokeKey(id);
      const response = await api.listKeys();
      setKeys(response.keys || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteKey(id);
      const response = await api.listKeys();
      setKeys(response.keys || []);
    } catch (err) {
      setError(err.message);
    }
  };

  if (!signedIn) {
    return <SignedOut />;
  }

  const sidebar = (
    <DashboardSidebar
      navGroups={navGroups}
      bottomItems={bottomItems}
      activeId={section}
      onSelect={handleSelect}
    />
  );

  return (
    <div
      className={cn(
        "flex h-screen w-full overflow-hidden bg-black",
        resolveTheme(theme) === "light" && "theme-light"
      )}
    >
      {/* Desktop sidebar */}
      <div
        className={cn(
          "hidden h-full transition-all duration-300 lg:block",
          sidebarOpen ? "w-[260px]" : "w-0 overflow-hidden"
        )}
      >
        {sidebar}
      </div>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/10 bg-ink-900/40 px-4">
          <div className="flex min-w-0 items-center gap-3">
            <button
              onClick={() => {
                if (window.innerWidth < 1024) {
                  setMobileOpen((v) => !v);
                } else {
                  setSidebarOpen((v) => !v);
                }
              }}
              className="rounded-md px-2 py-1.5 text-sm text-neutral-400 transition hover:bg-white/5 hover:text-white"
              aria-label="Toggle sidebar"
            >
              {sidebarOpen ? "⟨" : "⟩"}
            </button>
            <div className="flex min-w-0 items-center gap-2 text-sm text-neutral-500">
              <span className="truncate font-medium text-white">
                {SECTION_TITLES[section]}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {user?.name && (
              <span className="hidden text-sm text-neutral-400 sm:inline">
                {user.name}
              </span>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="mx-auto max-w-[1400px] space-y-8">
            {error && (
              <Card className="border-rose-500/20 bg-rose-500/[0.05] text-sm text-rose-300">
                {error}
              </Card>
            )}

            {newKey && (
              <NewKeyBanner
                apiKey={newKey}
                onDismiss={() => setNewKey(null)}
              />
            )}

            {section === "overview" && (
              <div className="space-y-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h1 className="text-2xl font-bold text-white">
                      Welcome back
                    </h1>
                    <p className="mt-1 text-sm text-neutral-400">
                      Here's how your API is performing.
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setSection("playground")}
                    >
                      Playground
                    </Button>
                    <Button size="sm" onClick={() => setSection("keys")}>
                      New key
                    </Button>
                  </div>
                </div>

                {loaded ? (
                  <>
                    <AdvancedStats
                      series={usage.series}
                      summary={summary}
                      requests={usage.recent}
                    />
                    <div className="grid gap-6 lg:grid-cols-3">
                      <ModelUsageCard items={modelUsage} />
                      <ActivityFeed items={activity} />
                      <QuickStartCard
                        items={[
                          {
                            label: "Create an API key",
                            done: keys.length > 0,
                          },
                          {
                            label: "Send your first analysis",
                            done: usage.summary.total > 0,
                          },
                          { label: "Try the playground", done: false },
                          { label: "Read the docs", done: false },
                        ]}
                      />
                    </div>
                  </>
                ) : (
                  <Card className="grid min-h-[240px] place-items-center text-sm text-neutral-500">
                    Loading your data…
                  </Card>
                )}
              </div>
            )}

            {section === "keys" && (
              <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
                <KeyCreator onCreated={handleCreated} onError={setError} />
                <Card className="p-0">
                  <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                    <h3 className="text-lg font-semibold text-white">
                      Your API keys
                    </h3>
                    <Badge tone="slate">{keys.length}</Badge>
                  </div>
                  {keys.length === 0 ? (
                    <div className="flex flex-col items-center justify-center px-5 py-16 text-center">
                      <p className="text-sm text-neutral-500">
                        No keys yet. Create your first key to call the endpoint.
                      </p>
                    </div>
                  ) : (
                    <div>
                      {keys.map((key) => (
                        <KeyRow
                          key={key.id}
                          apiKey={key}
                          onRevoke={handleRevoke}
                          onDelete={handleDelete}
                        />
                      ))}
                    </div>
                  )}
                </Card>
              </div>
            )}

            {section === "usage" && (
              <>
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
                  <StatCard
                    label="Total requests"
                    value={summary.total.toLocaleString()}
                  />
                  <StatCard
                    label="Analyses"
                    value={usage.series
                      .reduce((sum, day) => sum + day.analyses, 0)
                      .toLocaleString()}
                    tone="accent"
                  />
                  <StatCard
                    label="Function calls"
                    value={usage.series
                      .reduce((sum, day) => sum + day.agents, 0)
                      .toLocaleString()}
                    tone="green"
                  />
                  <StatCard
                    label="Errors"
                    value={summary.errors}
                    tone="amber"
                  />
                </div>
                <div className="grid gap-6 lg:grid-cols-2">
                  <Card>
                    <h3 className="mb-4 text-lg font-semibold text-white">
                      Requests over time
                    </h3>
                    <UsageAreaChart data={usage.series} />
                  </Card>
                  <Card>
                    <h3 className="mb-4 text-lg font-semibold text-white">
                      Requests by asset
                    </h3>
                    <SymbolBarChart data={breakdown} />
                  </Card>
                </div>
              </>
            )}

            {section === "playground" && <Playground />}
          </div>
        </div>
      </div>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/70"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full bg-black">
            {sidebar}
          </div>
        </div>
      )}

      <Settings
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onThemeChange={setTheme}
      />
    </div>
  );
}
