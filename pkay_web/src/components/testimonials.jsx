import { useEffect, useState } from "react";
import { cn } from "./ui.jsx";

const TESTIMONIALS = [
  {
    quote:
      "I've been searching for a solution like Pkay AI for YEARS. So glad I finally found one!",
    name: "Pete",
    role: "Sales Director",
    company: "RevenueRockets",
  },
  {
    quote: "I switched 5 years ago and never looked back.",
    name: "Andy",
    role: "DevOps Engineer",
    company: "CloudMasters",
  },
  {
    quote:
      "Pkay AI's customer service is unparalleled. They're there when we need them.",
    name: "Olivia",
    role: "Customer Success Manager",
    company: "ClientCare",
  },
  {
    quote: "Simple and intuitive. Our team was up to speed in a day.",
    name: "Marina",
    role: "HR Manager",
    company: "TalentForge",
  },
  {
    quote: "It's just the best. Period.",
    name: "Fernando",
    role: "UX Designer",
    company: "Studio Nine",
  },
  {
    quote: "The AI Agent Team replaced three separate tools for us.",
    name: "Raj",
    role: "CTO",
    company: "Streamline",
  },
  {
    quote: "From key to insight in minutes. Our analysts love it.",
    name: "Sofia",
    role: "Quant Lead",
    company: "Meridian",
  },
];

function initials(name) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function Card({ item, offset, isActive }) {
  const abs = Math.abs(offset);
  const hidden = abs > 2;
  const y = isActive ? 0 : abs % 2 === 0 ? 30 : -30;
  const scale = isActive ? 1 : 0.86 - (abs - 1) * 0.03;

  return (
    <article
      style={{
        transform: `translate(calc(-50% + ${offset * 300}px), calc(-50% + ${y}px)) rotate(${offset * 3}deg) scale(${scale})`,
        zIndex: 20 - abs,
        opacity: hidden ? 0 : 1,
        pointerEvents: hidden ? "none" : "auto",
      }}
      className={cn(
        "absolute left-1/2 top-1/2 w-[300px] rounded-2xl border p-6 transition-all duration-500 ease-out sm:w-[340px]",
        isActive
          ? "border-white/20 bg-white text-black shadow-2xl shadow-black/70"
          : "border-white/10 bg-ink-800/80 text-neutral-300"
      )}
      aria-hidden={!isActive}
    >
      <div className="flex items-center gap-3">
        <span
          className={cn(
            "grid h-11 w-11 shrink-0 place-items-center rounded-full text-sm font-bold",
            isActive ? "bg-black text-white" : "bg-white/10 text-white"
          )}
        >
          {initials(item.name)}
        </span>
        <span className="min-w-0">
          <span
            className={cn(
              "block truncate text-sm font-semibold",
              isActive ? "text-black" : "text-white"
            )}
          >
            {item.name}
          </span>
          <span
            className={cn(
              "block truncate text-xs",
              isActive ? "text-neutral-600" : "text-neutral-500"
            )}
          >
            {item.role} at {item.company}
          </span>
        </span>
      </div>

      <p
        className={cn(
          "mt-5 text-lg font-medium leading-relaxed",
          isActive ? "text-black" : "text-neutral-300"
        )}
      >
        &ldquo;{item.quote}&rdquo;
      </p>

      <p
        className={cn(
          "mt-6 text-xs italic",
          isActive ? "text-neutral-600" : "text-neutral-500"
        )}
      >
        — {item.name}, {item.role} at {item.company}
      </p>
    </article>
  );
}

export function StaggerTestimonials({ items = TESTIMONIALS }) {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const count = items.length;

  const go = (dir) => setActive((i) => (i + dir + count) % count);

  useEffect(() => {
    if (paused) return;
    const id = setInterval(() => setActive((i) => (i + 1) % count), 6000);
    return () => clearInterval(id);
  }, [paused, count]);

  return (
    <div
      className="relative select-none"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className="relative h-[420px] overflow-hidden [perspective:1400px]">
        {items.map((item, index) => {
          let offset = index - active;
          if (offset > count / 2) offset -= count;
          if (offset < -count / 2) offset += count;
          return (
            <Card
              key={`${item.name}-${index}`}
              item={item}
              offset={offset}
              isActive={offset === 0}
            />
          );
        })}
      </div>

      <div className="mt-6 flex items-center justify-center gap-4">
        <button
          onClick={() => go(-1)}
          aria-label="Previous testimonial"
          className="grid h-11 w-11 place-items-center rounded-xl border border-white/15 bg-white/5 text-lg text-neutral-300 transition hover:border-white/30 hover:text-white"
        >
          &larr;
        </button>
        <span className="font-mono text-xs text-neutral-500">
          {String(active + 1).padStart(2, "0")} /{" "}
          {String(count).padStart(2, "0")}
        </span>
        <button
          onClick={() => go(1)}
          aria-label="Next testimonial"
          className="grid h-11 w-11 place-items-center rounded-xl border border-white/15 bg-white/5 text-lg text-neutral-300 transition hover:border-white/30 hover:text-white"
        >
          &rarr;
        </button>
      </div>
    </div>
  );
}
