import { useEffect, useRef, useState } from "react";
import { cn } from "./ui.jsx";

export function SpotlightCard({ className, children, ...props }) {
  const ref = useRef(null);

  const onMouseMove = (event) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--mx", `${event.clientX - rect.left}px`);
    el.style.setProperty("--my", `${event.clientY - rect.top}px`);
  };

  return (
    <div
      ref={ref}
      onMouseMove={onMouseMove}
      className={cn(
        "spotlight-card rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-sm transition-colors duration-300 hover:border-white/20",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function Marquee({ items, className }) {
  const doubled = [...items, ...items];
  return (
    <div
      className={cn(
        "group relative flex overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_12%,black_88%,transparent)]",
        className
      )}
    >
      <div className="flex shrink-0 animate-marquee items-center gap-12 pr-12 group-hover:[animation-play-state:paused]">
        {doubled.map((item, index) => {
          const isObject = typeof item === "object" && item !== null;
          const label = isObject ? item.label : item;
          const logo = isObject ? item.logo : null;
          return (
            <span
              key={`${label}-${index}`}
              className="flex items-center gap-3 whitespace-nowrap"
            >
              {logo && (
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white">
                  <img
                    src={logo}
                    alt={`${label} logo`}
                    className="h-4 w-4"
                    loading="lazy"
                  />
                </span>
              )}
              <span className="text-sm font-semibold uppercase tracking-[0.22em] text-neutral-500">
                {label}
              </span>
            </span>
          );
        })}
      </div>
    </div>
  );
}

export function Reveal({ children, className, delay = 0, as: Tag = "div" }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={cn("reveal", visible && "is-visible", className)}
    >
      {children}
    </Tag>
  );
}

export function NumberTicker({
  value,
  prefix = "",
  suffix = "",
  decimals = 0,
  duration = 1400,
  className,
}) {
  const ref = useRef(null);
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let frame;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      observer.disconnect();
      const start = performance.now();
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setDisplay(value * eased);
        if (progress < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    });
    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [value, duration]);

  return (
    <span ref={ref} className={className}>
      {prefix}
      {display.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </span>
  );
}

export function AuroraBackground({ className }) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden",
        className
      )}
    >
      <div className="absolute -left-40 top-[-10%] h-[32rem] w-[32rem] animate-aurora rounded-full bg-brand-600/20 blur-[120px]" />
      <div className="absolute right-[-10%] top-[10%] h-[28rem] w-[28rem] animate-aurora rounded-full bg-accent-500/15 blur-[120px] [animation-delay:-6s]" />
      <div className="absolute bottom-[-20%] left-1/3 h-[30rem] w-[30rem] animate-aurora rounded-full bg-brand-500/10 blur-[130px] [animation-delay:-3s]" />
    </div>
  );
}

export function GlowRing({ className }) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 rounded-[inherit]",
        className
      )}
      style={{
        background:
          "radial-gradient(600px circle at 50% 0%, rgba(255,255,255,0.08), transparent 60%)",
      }}
    />
  );
}
