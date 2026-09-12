import { Badge, Button, Card, SectionHeading } from "../components/ui.jsx";

const values = [
  {
    title: "Signal, not noise",
    text: "Ten agents and a weighted consensus replace gut feeling with a repeatable process.",
  },
  {
    title: "Developer first",
    text: "One endpoint, clear errors and keys you manage yourself. No connector sprawl.",
  },
  {
    title: "Always available",
    text: "Live data with a deterministic demo fallback so an analysis never fails silently.",
  },
];

export default function About() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="max-w-3xl">
        <p className="mb-5 text-sm font-semibold uppercase tracking-[0.2em] text-neutral-500">
          About
        </p>
        <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
          We build tools that make{" "}
          <span className="text-gradient">markets legible</span>
        </h1>
        <p className="mt-5 text-lg leading-relaxed text-neutral-400">
          Pkay AI is a multi-asset trading analysis platform. We package a team
          of specialized AI agents behind a single endpoint so anyone can add
          institutional-grade analysis to their product.
        </p>
      </div>

      <div className="mt-16 grid gap-6 md:grid-cols-3">
        {values.map((value, index) => (
          <Card key={value.title} hover>
            <span className="font-mono text-sm text-neutral-600">
              {String(index + 1).padStart(2, "0")}
            </span>
            <h3 className="mt-4 text-lg font-semibold text-white">
              {value.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-neutral-400">
              {value.text}
            </p>
          </Card>
        ))}
      </div>

      <section className="mt-20">
        <SectionHeading
          eyebrow="Open source"
          title="Free to use under the MIT License"
          subtitle="Pkay AI is released under the MIT License — use it, modify it and ship it with attribution."
        />
        <div className="mt-10 flex justify-center">
          <Button
            href="https://github.com/Sultanrayan/pkay-ai-analysis"
            variant="secondary"
            size="lg"
          >
            View on GitHub
          </Button>
        </div>
      </section>

      {/* Contact */}
      <section id="contact" className="mt-24 scroll-mt-24">
        <Card className="grid gap-10 p-10 lg:grid-cols-2 lg:p-14">
          <div>
            <h2 className="text-3xl font-bold text-white">Get in touch</h2>
            <p className="mt-4 leading-relaxed text-neutral-400">
              Questions about the endpoint, pricing or a custom integration? We
              usually reply within a day.
            </p>
            <div className="mt-8 space-y-4">
              <a
                href="mailto:errorkruzer1@gmail.com"
                className="block text-neutral-300 transition hover:text-white"
              >
                <span className="block text-xs uppercase tracking-wider text-neutral-500">
                  Email
                </span>
                errorkruzer1@gmail.com
              </a>
              <a
                href="https://t.me/spcaeechoo"
                target="_blank"
                rel="noreferrer"
                className="block text-neutral-300 transition hover:text-white"
              >
                <span className="block text-xs uppercase tracking-wider text-neutral-500">
                  Telegram
                </span>
                @spcaeechoo
              </a>
              <a
                href="https://github.com/Sultanrayan/pkay-ai-analysis/issues"
                target="_blank"
                rel="noreferrer"
                className="block text-neutral-300 transition hover:text-white"
              >
                <span className="block text-xs uppercase tracking-wider text-neutral-500">
                  GitHub
                </span>
                Open an issue
              </a>
            </div>
          </div>

          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              e.currentTarget.reset();
              alert("Thanks! This demo form does not send yet.");
            }}
          >
            <div>
              <label className="mb-1.5 block text-sm font-medium text-neutral-300">
                Name
              </label>
              <input
                required
                className="w-full rounded-xl border border-white/10 bg-ink-900/70 px-4 py-2.5 text-sm text-white placeholder:text-neutral-600 focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/10"
                placeholder="Ada Lovelace"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-neutral-300">
                Email
              </label>
              <input
                required
                type="email"
                className="w-full rounded-xl border border-white/10 bg-ink-900/70 px-4 py-2.5 text-sm text-white placeholder:text-neutral-600 focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/10"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-neutral-300">
                Message
              </label>
              <textarea
                required
                rows={4}
                className="w-full resize-none rounded-xl border border-white/10 bg-ink-900/70 px-4 py-2.5 text-sm text-white placeholder:text-neutral-600 focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/10"
                placeholder="Tell us what you are building…"
              />
            </div>
            <Button type="submit" className="w-full">
              Send message
            </Button>
          </form>
        </Card>
      </section>
    </div>
  );
}
