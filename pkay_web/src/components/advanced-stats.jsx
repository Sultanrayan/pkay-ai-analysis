import { Card } from "./ui.jsx";
import { PerformanceAreaChart } from "./charts.jsx";
import { Sparkline } from "./dashboard-widgets.jsx";

function Trend({ value }) {
  const up = value >= 0;
  return (
    <span
      className={
        up
          ? "text-sm font-semibold text-emerald-400"
          : "text-sm font-semibold text-rose-400"
      }
    >
      {up ? "+" : ""}
      {value}%
    </span>
  );
}

export default function AdvancedStats({ series, summary, requests }) {
  const totalAnalyses = series.reduce((sum, day) => sum + day.analyses, 0);
  const avgLatency = requests.length
    ? Math.round(
        requests.reduce((sum, req) => sum + req.latency, 0) / requests.length
      )
    : 0;
  const coverage = Math.min(
    99,
    Math.round((totalAnalyses / Math.max(summary.total, 1)) * 100)
  );

  const kpis = [
    {
      label: "Total requests",
      value: summary.total.toLocaleString(),
      change: summary.change,
      spark: series.map((day) => day.requests),
    },
    {
      label: "Analyses",
      value: totalAnalyses.toLocaleString(),
      change: 4.2,
      spark: series.map((day) => day.analyses),
    },
    {
      label: "Avg. response time",
      value: `${avgLatency}ms`,
      change: -8.1,
      spark: series.map((day, i) => 240 - (day.requests % 5) * 12 + i),
    },
    {
      label: "Success rate",
      value: `${summary.successRate}%`,
      change: 1.2,
      spark: series.map((day) => 100 - day.errors),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Platform performance */}
        <Card className="lg:col-span-2">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-white">
                Platform Performance
              </h3>
              <p className="mt-1 text-xs uppercase tracking-[0.18em] text-neutral-500">
                Last 14 days growth
              </p>
            </div>
            <div className="text-right">
              <div className="flex items-center justify-end gap-3">
                <span className="text-2xl font-bold text-white">
                  {summary.total.toLocaleString()}
                </span>
                <Trend value={summary.change} />
              </div>
              <p className="mt-1 text-sm text-neutral-500">
                Total requests this period
              </p>
            </div>
          </div>
          <div className="mt-6">
            <PerformanceAreaChart data={series} />
          </div>
        </Card>

        {/* Right column */}
        <div className="flex flex-col gap-6">
          <div className="rounded-2xl border border-white/20 bg-white p-6 text-black">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">
              Primary goal
            </p>
            <p className="mt-3 text-lg font-semibold text-black">
              Analysis coverage
            </p>
            <div className="mt-6 flex items-end justify-between">
              <span className="text-4xl font-extrabold text-black">
                {coverage}%
              </span>
              <span className="pb-1 text-sm text-neutral-500">
                Target: 75%
              </span>
            </div>
            <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-black/10">
              <div
                className="h-full rounded-full bg-black"
                style={{ width: `${coverage}%` }}
              />
            </div>
          </div>

          <Card className="flex-1">
            <p className="text-sm font-semibold text-white">Usage growth</p>
            <p className="mt-3 text-sm leading-relaxed text-neutral-400">
              Request volume is up{" "}
              <span className="font-semibold text-emerald-400">
                {summary.change >= 0 ? "+" : ""}
                {summary.change}%
              </span>{" "}
              compared to the previous period, with{" "}
              {summary.errors} errors recorded across the window.
            </p>
          </Card>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <Card key={kpi.label} className="p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-neutral-500">
              {kpi.label}
            </p>
            <div className="mt-3 flex items-end justify-between">
              <span className="text-2xl font-bold text-white">
                {kpi.value}
              </span>
              <Trend value={kpi.change} />
            </div>
            <Sparkline data={kpi.spark} className="mt-4 h-10" />
          </Card>
        ))}
      </div>
    </div>
  );
}
