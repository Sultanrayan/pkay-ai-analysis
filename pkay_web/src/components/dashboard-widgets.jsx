import { Badge, Card, cn } from "./ui.jsx";
import { SpotlightCard } from "./premium.jsx";

export function Sparkline({ data, className, stroke = "#ffffff" }) {
  const values = data.length > 1 ? data : [0, 0];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 120;
  const h = 36;
  const points = values.map((value, index) => {
    const x = (index / (values.length - 1)) * w;
    const y = h - ((value - min) / range) * (h - 8) - 4;
    return [x, y];
  });
  const line = points.map(([x, y]) => `${x},${y}`).join(" ");
  const area = `0,${h} ${line} ${w},${h}`;

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      className={cn("h-10 w-full", className)}
      aria-hidden="true"
    >
      <polygon points={area} fill={stroke} opacity="0.12" />
      <polyline
        points={line}
        fill="none"
        stroke={stroke}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

export function ProgressRing({ value, size = 104, stroke = 9, label }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(value, 100) / 100) * circumference;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#ffffff"
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <div className="text-center">
          <p className="text-xl font-bold text-white">{value}%</p>
          {label && (
            <p className="text-[10px] uppercase tracking-wider text-neutral-500">
              {label}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function EndpointStatusCard({
  method,
  endpoint,
  requests,
  successRate,
  series,
  status = "operational",
}) {
  return (
    <SpotlightCard className="p-5">
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex min-w-0 items-center gap-2">
          <Badge tone="green">{method}</Badge>
          <code className="truncate font-mono text-sm text-neutral-200">
            {endpoint}
          </code>
        </span>
        <span className="inline-flex shrink-0 items-center gap-1.5 text-xs text-emerald-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          {status}
        </span>
      </div>

      <div className="mt-5 flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-white">{requests}</p>
          <p className="text-xs text-neutral-500">requests this month</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-white">{successRate}%</p>
          <p className="text-xs text-neutral-500">success rate</p>
        </div>
      </div>

      <Sparkline data={series} className="mt-4 h-12" />
    </SpotlightCard>
  );
}

export function ModelUsageCard({ items }) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Model usage</h3>
        <span className="text-xs text-neutral-500">this month</span>
      </div>
      <div className="mt-5 space-y-4">
        {items.map((item) => (
          <div key={item.name}>
            <div className="flex items-center justify-between text-xs">
              <span className="text-neutral-300">{item.name}</span>
              <span className="text-neutral-500">{item.pct}%</span>
            </div>
            <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-white"
                style={{ width: `${item.pct}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function ActivityFeed({ items, className }) {
  return (
    <Card className={cn("p-5", className)}>
      <h3 className="text-sm font-semibold text-white">Recent activity</h3>
      <ul className="mt-4 space-y-4">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-white/60" />
            <div className="min-w-0">
              <p className="text-sm text-neutral-200">{item.title}</p>
              <p className="text-xs text-neutral-500">{item.time}</p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function QuickStartCard({ items }) {
  const done = items.filter((item) => item.done).length;
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Quick start</h3>
        <span className="text-xs text-neutral-500">
          {done}/{items.length}
        </span>
      </div>
      <ul className="mt-4 space-y-3">
        {items.map((item) => (
          <li key={item.label} className="flex items-center gap-3 text-sm">
            <span
              className={cn(
                "grid h-5 w-5 shrink-0 place-items-center rounded-full border text-[11px]",
                item.done
                  ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
                  : "border-white/15 bg-white/5 text-neutral-500"
              )}
            >
              {item.done ? "✓" : ""}
            </span>
            <span
              className={cn(
                item.done ? "text-neutral-400 line-through" : "text-neutral-200"
              )}
            >
              {item.label}
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function StatusPill({ label = "All systems operational" }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-300">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
      {label}
    </span>
  );
}
