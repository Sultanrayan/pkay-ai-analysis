import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const axis = {
  stroke: "#475569",
  fontSize: 12,
  tickLine: false,
  axisLine: false,
};

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-white/10 bg-ink-900/95 px-3 py-2 text-xs shadow-xl backdrop-blur">
      <p className="mb-1 font-semibold text-white">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="text-slate-400">
          <span
            className="mr-1.5 inline-block h-2 w-2 rounded-full"
            style={{ background: entry.color }}
          />
          {entry.name}:{" "}
          <span className="font-medium text-slate-200">{entry.value}</span>
        </p>
      ))}
    </div>
  );
}

export function UsageAreaChart({ data, height = 280 }) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="requestsFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ffffff" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ffffff" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="analysesFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#9ca3af" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#9ca3af" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
          <XAxis dataKey="date" {...axis} />
          <YAxis {...axis} />
          <Tooltip content={<ChartTooltip />} />
          <Area
            type="monotone"
            dataKey="requests"
            name="Requests"
            stroke="#ffffff"
            strokeWidth={2}
            fill="url(#requestsFill)"
          />
          <Area
            type="monotone"
            dataKey="analyses"
            name="Analyses"
            stroke="#9ca3af"
            strokeWidth={2}
            fill="url(#analysesFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

const BAR_COLORS = ["#ffffff", "#d4d4d4", "#a3a3a3", "#737373"];

export function SymbolBarChart({ data, height = 280 }) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="symbol" {...axis} />
          <YAxis {...axis} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(99,102,241,0.08)" }} />
          <Bar dataKey="requests" name="Requests" radius={[6, 6, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={entry.symbol} fill={BAR_COLORS[index % BAR_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PerformanceAreaChart({ data, height = 240 }) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 8, left: -18, bottom: 0 }}
        >
          <defs>
            <linearGradient id="perfFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ffffff" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#ffffff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
          <XAxis dataKey="date" {...axis} />
          <YAxis {...axis} />
          <Tooltip content={<ChartTooltip />} />
          <Area
            type="monotone"
            dataKey="requests"
            name="Requests"
            stroke="#ffffff"
            strokeWidth={2}
            fill="url(#perfFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
