import { Link } from "react-router-dom";
import Logo from "./logo.jsx";

const columns = [
  {
    title: "Product",
    links: [
      { label: "Features", to: "/features" },
      { label: "How it works", to: "/how-it-works" },
      { label: "Pricing", to: "/pricing" },
      { label: "Dashboard", to: "/dashboard" },
    ],
  },
  {
    title: "Developers",
    links: [
      { label: "Documentation", to: "/docs" },
      { label: "API reference", to: "/docs#endpoint" },
      { label: "Models", to: "/docs#models" },
      { label: "API keys", to: "/dashboard" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", to: "/about" },
      { label: "Contact", to: "/about#contact" },
      {
        label: "GitHub",
        href: "https://github.com/Sultanrayan/pkay-ai-analysis",
      },
      {
        label: "License (MIT)",
        href: "https://github.com/Sultanrayan/pkay-ai-analysis/blob/main/LICENSE.md",
      },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="relative mt-24 overflow-hidden border-t border-white/10 bg-ink-900/40">
      <div className="mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <Logo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-neutral-400">
              Multi-asset AI trading analysis. Call one endpoint, get the AI
              Agent Team and analysis features.
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
              <a
                href="https://github.com/Sultanrayan/pkay-ai-analysis"
                target="_blank"
                rel="noreferrer"
                className="text-neutral-400 transition hover:text-white"
              >
                GitHub
              </a>
              <a
                href="https://t.me/spcaeechoo"
                target="_blank"
                rel="noreferrer"
                className="text-neutral-400 transition hover:text-white"
              >
                Telegram
              </a>
              <a
                href="mailto:errorkruzer1@gmail.com"
                className="text-neutral-400 transition hover:text-white"
              >
                Email
              </a>
            </div>
          </div>

          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-semibold text-white">{col.title}</h4>
              <ul className="mt-4 space-y-3">
                {col.links.map((link) => (
                  <li key={link.label}>
                    {link.to ? (
                      <Link
                        to={link.to}
                        className="text-sm text-neutral-400 transition hover:text-white"
                      >
                        {link.label}
                      </Link>
                    ) : (
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm text-neutral-400 transition hover:text-white"
                      >
                        {link.label}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Flickering tagline */}
      <div
        className="pointer-events-none mt-16 select-none px-2 sm:px-4"
        aria-hidden="true"
      >
        <p className="flicker-text whitespace-nowrap text-center text-[clamp(1.75rem,8vw,7rem)] font-extrabold leading-[0.95] tracking-tight">
          Analyze every market
        </p>
      </div>

      <div className="mt-8 border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-6 sm:flex-row sm:px-6 lg:px-8">
          <p className="text-sm text-neutral-500">
            © {new Date().getFullYear()} Pkay AI. Released under the MIT License.
          </p>
          <p className="text-xs text-neutral-600">
            Signal-only analytics. Not financial advice.
          </p>
        </div>
      </div>
    </footer>
  );
}
