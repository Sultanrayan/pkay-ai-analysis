import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Button, cn } from "./ui.jsx";
import Logo from "./logo.jsx";
import { AuthModal } from "./auth.jsx";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/how-it-works", label: "How it works" },
  { to: "/features", label: "Features" },
  { to: "/pricing", label: "Pricing" },
  { to: "/docs", label: "Docs" },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 transition-all duration-300",
        scrolled
          ? "border-b border-white/10 bg-black/80 backdrop-blur-xl"
          : "border-b border-transparent"
      )}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo />

        <nav className="hidden items-center gap-1 lg:flex">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                cn(
                  "rounded-lg px-3.5 py-2 text-sm font-medium transition-colors",
                  isActive ? "text-white" : "text-neutral-400 hover:text-white"
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <Button variant="ghost" size="sm" onClick={() => setAuthOpen(true)}>
            Sign in
          </Button>
          <Button to="/dashboard" size="sm">
            Dashboard
          </Button>
        </div>

        <button
          onClick={() => setOpen((v) => !v)}
          className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-neutral-200 lg:hidden"
          aria-label="Toggle navigation"
        >
          {open ? "Close" : "Menu"}
        </button>
      </div>

      {open && (
        <div className="border-t border-white/10 bg-black/95 px-4 pb-6 pt-4 backdrop-blur-xl lg:hidden">
          <nav className="flex flex-col gap-1">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  cn(
                    "rounded-lg px-3 py-2.5 text-sm font-medium",
                    isActive
                      ? "bg-white/5 text-white"
                      : "text-neutral-400 hover:bg-white/5 hover:text-white"
                  )
                }
              >
                {link.label}
              </NavLink>
            ))}
            <Button
              variant="secondary"
              className="mt-3 w-full"
              onClick={() => setAuthOpen(true)}
            >
              Sign in
            </Button>
            <Button to="/dashboard" className="mt-2 w-full">
              Open Dashboard
            </Button>
          </nav>
        </div>
      )}

      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </header>
  );
}
