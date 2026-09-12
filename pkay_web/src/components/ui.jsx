import { useState } from "react";
import { Link } from "react-router-dom";

export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

const buttonVariants = {
  primary:
    "bg-white text-black shadow-lg shadow-black/50 hover:bg-neutral-200",
  secondary:
    "border border-white/15 bg-white/[0.03] text-white hover:bg-white/10 hover:border-white/30",
  ghost: "text-neutral-400 hover:text-white hover:bg-white/5",
  danger:
    "border border-rose-500/40 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20",
};

const buttonSizes = {
  sm: "h-9 px-3.5 text-sm",
  md: "h-11 px-5 text-sm",
  lg: "h-12 px-6 text-base",
};

export function Button({
  as,
  to,
  href,
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}) {
  const classes = cn(
    "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40 disabled:cursor-not-allowed disabled:opacity-50",
    buttonVariants[variant],
    buttonSizes[size],
    className
  );

  if (to) {
    return (
      <Link to={to} className={classes} {...props}>
        {children}
      </Link>
    );
  }
  if (href) {
    return (
      <a href={href} className={classes} {...props}>
        {children}
      </a>
    );
  }
  const Tag = as || "button";
  return (
    <Tag className={classes} {...props}>
      {children}
    </Tag>
  );
}

export function Card({ className, children, hover = false, ...props }) {
  return (
    <div
      className={cn(
        "spotlight-card rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm",
        hover && "card-hover",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function Badge({ children, className, tone = "brand" }) {
  const tones = {
    brand: "border-white/20 bg-white/5 text-neutral-200",
    accent: "border-white/20 bg-white/5 text-neutral-200",
    green: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    amber: "border-amber-500/30 bg-amber-500/10 text-amber-300",
    slate: "border-white/15 bg-white/5 text-neutral-300",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  subtitle,
  align = "center",
  className,
}) {
  return (
    <div
      className={cn(
        "max-w-2xl",
        align === "center" && "mx-auto text-center",
        className
      )}
    >
      {eyebrow && (
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-neutral-500">
          {eyebrow}
        </p>
      )}
      <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-base leading-relaxed text-neutral-400">
          {subtitle}
        </p>
      )}
    </div>
  );
}

export function CodeBlock({ code, language = "bash", className }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-xl border border-white/10 bg-ink-900/80",
        className
      )}
    >
      <div className="flex items-center justify-between border-b border-white/5 px-4 py-2">
        <span className="font-mono text-xs uppercase tracking-wider text-neutral-500">
          {language}
        </span>
        <button
          onClick={copy}
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-neutral-400 transition hover:bg-white/5 hover:text-white"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed">
        <code className="font-mono text-neutral-300">{code}</code>
      </pre>
    </div>
  );
}

export function StatCard({ label, value, hint, tone = "brand" }) {
  const tones = {
    brand: "from-white/10 to-white/0",
    accent: "from-white/10 to-white/0",
    green: "from-emerald-500/15 to-emerald-500/0",
    amber: "from-amber-500/15 to-amber-500/0",
  };
  return (
    <Card className="relative overflow-hidden">
      <div
        className={cn(
          "pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br blur-2xl",
          tones[tone]
        )}
      />
      <p className="text-sm font-medium text-neutral-400">{label}</p>
      <p className="mt-4 text-3xl font-bold text-white">{value}</p>
      {hint && <p className="mt-1 text-xs text-neutral-500">{hint}</p>}
    </Card>
  );
}
