import { useEffect, useState } from "react";
import { cn } from "./ui.jsx";
import Logo from "./logo.jsx";
import { authUrl } from "../lib/api.js";

export function GoogleButton({ onClick, loading, label }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      className="flex h-11 w-full items-center justify-center gap-3 rounded-xl bg-white px-5 text-sm font-semibold text-black transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-70"
    >
      <img src="/google.svg" alt="Google" className="h-5 w-5" />
      {loading ? "Connecting…" : label}
    </button>
  );
}

export function AuthBox({
  initialMode = "signin",
  onClose,
  onAuthenticated,
  className,
}) {
  const [mode, setMode] = useState(initialMode);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  const isSignIn = mode === "signin";

  const handleGoogle = () => {
    setLoading(true);
    window.location.href = authUrl;
  };

  return (
    <div
      className={cn(
        "relative w-full max-w-sm rounded-2xl border border-white/10 bg-ink-900 p-7 shadow-2xl shadow-black",
        className
      )}
    >
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 rounded-lg px-2 py-1 text-xs text-neutral-500 transition hover:bg-white/5 hover:text-white"
        >
          Close
        </button>
      )}

      <div className="flex justify-center">
        <Logo asLink={false} />
      </div>

      <h2 className="mt-6 text-center text-xl font-bold text-white">
        {isSignIn ? "Welcome back" : "Create your account"}
      </h2>
      <p className="mt-1.5 text-center text-sm text-neutral-400">
        {isSignIn
          ? "Sign in to your Pkay AI dashboard."
          : "Register to start using the AI Agent Team."}
      </p>

      {/* Mode toggle */}
      <div className="mt-6 flex rounded-xl border border-white/10 bg-white/[0.03] p-1">
        {[
          { value: "signin", label: "Sign in" },
          { value: "register", label: "Register" },
        ].map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setMode(opt.value)}
            className={cn(
              "flex-1 rounded-lg px-3 py-2 text-sm font-medium transition",
              mode === opt.value
                ? "bg-white text-black"
                : "text-neutral-400 hover:text-white"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        <GoogleButton
          onClick={handleGoogle}
          loading={loading}
          label={
            isSignIn ? "Continue with Google" : "Sign up with Google"
          }
        />
      </div>

      <p className="mt-4 text-center text-xs text-neutral-500">
        Google is the only sign-in method. No passwords, ever.
      </p>

      <div className="mt-6 border-t border-white/10 pt-4">
        <p className="text-center text-xs leading-relaxed text-neutral-600">
          By continuing you agree to our{" "}
          <a href="/about" className="text-neutral-400 hover:text-white">
            Terms
          </a>{" "}
          and{" "}
          <a href="/about" className="text-neutral-400 hover:text-white">
            Privacy Policy
          </a>
          .
        </p>
      </div>
    </div>
  );
}

export function AuthModal({ open, onClose, initialMode = "signin" }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <AuthBox
        initialMode={initialMode}
        onClose={onClose}
        onAuthenticated={onClose}
        className="relative"
      />
    </div>
  );
}
