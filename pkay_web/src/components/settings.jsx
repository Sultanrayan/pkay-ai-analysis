import { useEffect, useState } from "react";
import { Button, Card, cn } from "./ui.jsx";
import { MODELS } from "../lib/models.js";
import { api } from "../lib/api.js";

const TABS = [
  { id: "profile", label: "Profile" },
  { id: "account", label: "Account" },
  { id: "notifications", label: "Notifications" },
  { id: "appearance", label: "Appearance" },
  { id: "api", label: "API defaults" },
  { id: "security", label: "Security" },
];

const NOTIFICATION_KEYS = [
  ["analysisComplete", "Analysis complete", "Get notified when an analysis finishes."],
  ["sniperAlerts", "Sniper alerts", "Signal-only memecoin opportunities."],
  ["productUpdates", "Product updates", "New models, features and improvements."],
  ["weeklyDigest", "Weekly digest", "A summary of your usage every Monday."],
  ["securityAlerts", "Security alerts", "Sign-ins and API key changes."],
];

function Field({ label, hint, ...props }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-neutral-300">
        {label}
      </span>
      <input
        className="w-full rounded-xl border border-white/10 bg-ink-900/70 px-4 py-2.5 text-sm text-white placeholder:text-neutral-600 focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/10"
        {...props}
      />
      {hint && <span className="mt-1 block text-xs text-neutral-600">{hint}</span>}
    </label>
  );
}

function SelectField({ label, options, ...props }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-neutral-300">
        {label}
      </span>
      <select
        className="w-full rounded-xl border border-white/10 bg-ink-900/70 px-4 py-2.5 text-sm text-white focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/10"
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} className="bg-black">
            {opt.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Toggle({ checked, onChange, label, description }) {
  return (
    <div className="flex items-center justify-between gap-4 py-4">
      <div className="min-w-0">
        <p className="text-sm font-medium text-white">{label}</p>
        {description && (
          <p className="mt-0.5 text-xs text-neutral-500">{description}</p>
        )}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full border transition",
          checked ? "border-white/40 bg-white" : "border-white/15 bg-white/10"
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 h-5 w-5 rounded-full transition-all",
            checked ? "left-[22px] bg-black" : "left-0.5 bg-white"
          )}
        />
      </button>
    </div>
  );
}

function Segmented({ options, value, onChange }) {
  return (
    <div className="inline-flex rounded-xl border border-white/10 bg-white/[0.03] p-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={cn(
            "rounded-lg px-3.5 py-1.5 text-sm transition",
            value === opt.value
              ? "bg-white text-black"
              : "text-neutral-400 hover:text-white"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function PasswordModal({ onClose }) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (next.length < 8) {
      setError("New password must be at least 8 characters");
      return;
    }
    if (next !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setSaving(true);
    try {
      await api.changePassword({
        current_password: current,
        new_password: next,
      });
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-full max-w-sm rounded-2xl border border-white/10 bg-ink-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-white">
            Change password
          </h3>
          <button
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-xs text-neutral-500 transition hover:bg-white/5 hover:text-white"
          >
            Close
          </button>
        </div>

        {done ? (
          <div className="mt-5">
            <p className="text-sm text-emerald-400">Password updated.</p>
            <Button className="mt-4 w-full" onClick={onClose}>
              Done
            </Button>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-5 space-y-4">
            <Field
              label="Current password"
              type="password"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              placeholder="Leave blank if none set"
            />
            <Field
              label="New password"
              type="password"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              placeholder="At least 8 characters"
            />
            <Field
              label="Confirm new password"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
            {error && <p className="text-sm text-rose-400">{error}</p>}
            <Button type="submit" disabled={saving} className="w-full">
              {saving ? "Saving…" : "Update password"}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}

export default function Settings({
  open = false,
  onClose = () => {},
  onThemeChange = () => {},
}) {
  const [tab, setTab] = useState("profile");
  const [user, setUser] = useState(null);
  const [settings, setSettings] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [passwordOpen, setPasswordOpen] = useState(false);

  useEffect(() => {
    if (!open) return undefined;
    let active = true;
    setStatus("");
    setError("");
    Promise.all([api.me(), api.getSettings()])
      .then(([me, prefs]) => {
        if (!active) return;
        setUser(me);
        setSettings(prefs);
        onThemeChange(prefs.theme);
      })
      .catch((err) => {
        if (active) setError(err.message);
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const update = async (patch) => {
    setSettings((prev) => ({ ...prev, ...patch }));
    setStatus("Saving…");
    setError("");
    try {
      const updated = await api.updateSettings(patch);
      setSettings(updated);
      setStatus("Saved");
      setTimeout(() => setStatus(""), 1500);
    } catch (err) {
      setError(err.message);
      setStatus("");
    }
  };

  const setTheme = (value) => {
    onThemeChange(value);
    update({ theme: value });
  };

  const toggleNotification = (key, value) => {
    const notifications = { ...(settings?.notifications || {}), [key]: value };
    update({ notifications });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-white/10 bg-ink-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-white">Settings</h2>
            <p className="text-xs text-neutral-500">
              Manage your account, preferences and API defaults.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {status && (
              <span className="text-xs text-emerald-400">{status}</span>
            )}
            <button
              onClick={onClose}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-sm text-neutral-300 transition hover:bg-white/5 hover:text-white"
            >
              Close
            </button>
          </div>
        </div>

        <div className="overflow-y-auto p-6">
          {error && (
            <Card className="mb-4 border-rose-500/20 bg-rose-500/[0.05] text-sm text-rose-300">
              {error}
            </Card>
          )}

          <div className="grid gap-8 lg:grid-cols-[200px_1fr]">
            <nav className="flex gap-2 overflow-x-auto pb-2 lg:sticky lg:top-0 lg:flex-col lg:overflow-visible lg:pb-0">
              {TABS.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setTab(item.id)}
                  className={cn(
                    "whitespace-nowrap rounded-lg px-3.5 py-2 text-left text-sm transition",
                    tab === item.id
                      ? "bg-white/10 font-medium text-white"
                      : "text-neutral-500 hover:bg-white/5 hover:text-white"
                  )}
                >
                  {item.label}
                </button>
              ))}
            </nav>

            <div className="min-w-0 space-y-6">
              {!settings ? (
                <Card className="text-sm text-neutral-500">
                  Loading your settings…
                </Card>
              ) : (
                <>
                  {tab === "profile" && (
                    <Card className="p-6">
                      <h3 className="text-base font-semibold text-white">
                        Profile
                      </h3>
                      <p className="mt-1 text-sm text-neutral-400">
                        This account is managed by Google.
                      </p>
                      <div className="mt-5 flex items-center gap-4">
                        {user?.picture ? (
                          <img
                            src={user.picture}
                            alt={user.name || "avatar"}
                            className="h-14 w-14 rounded-full"
                          />
                        ) : (
                          <span className="grid h-14 w-14 place-items-center rounded-full bg-white text-lg font-bold text-black">
                            {(user?.name || user?.email || "P")
                              .charAt(0)
                              .toUpperCase()}
                          </span>
                        )}
                        <div>
                          <p className="font-medium text-white">
                            {user?.name || "—"}
                          </p>
                          <p className="text-sm text-neutral-400">
                            {user?.email || "—"}
                          </p>
                        </div>
                      </div>
                    </Card>
                  )}

                  {tab === "account" && (
                    <Card className="p-6">
                      <h3 className="text-base font-semibold text-white">
                        Account
                      </h3>
                      <p className="mt-1 text-sm text-neutral-400">
                        Regional preferences.
                      </p>
                      <div className="mt-6 grid gap-4 sm:grid-cols-2">
                        <SelectField
                          label="Language"
                          value={settings.language}
                          onChange={(e) =>
                            update({ language: e.target.value })
                          }
                          options={[
                            { value: "en", label: "English" },
                            { value: "kh", label: "Khmer" },
                          ]}
                        />
                        <SelectField
                          label="Currency"
                          value={settings.currency}
                          onChange={(e) =>
                            update({ currency: e.target.value })
                          }
                          options={[
                            { value: "usd", label: "USD" },
                            { value: "eur", label: "EUR" },
                            { value: "khr", label: "KHR" },
                          ]}
                        />
                        <SelectField
                          label="Timezone"
                          value={settings.timezone}
                          onChange={(e) =>
                            update({ timezone: e.target.value })
                          }
                          options={[
                            { value: "utc", label: "UTC" },
                            { value: "ict", label: "Asia/Phnom_Penh (ICT)" },
                            { value: "est", label: "America/New_York (EST)" },
                          ]}
                        />
                      </div>
                      <div className="mt-6 flex items-center justify-between border-t border-white/5 pt-4">
                        <div>
                          <p className="text-sm font-medium text-white">
                            Password
                          </p>
                          <p className="text-xs text-neutral-500">
                            Add a password to your account
                          </p>
                        </div>
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={() => setPasswordOpen(true)}
                        >
                          Change password
                        </Button>
                      </div>
                    </Card>
                  )}

                  {tab === "notifications" && (
                    <Card className="p-6">
                      <h3 className="text-base font-semibold text-white">
                        Notifications
                      </h3>
                      <p className="mt-1 text-sm text-neutral-400">
                        Choose what you want to hear about.
                      </p>
                      <div className="mt-2 divide-y divide-white/5">
                        {NOTIFICATION_KEYS.map(([key, label, description]) => (
                          <Toggle
                            key={key}
                            label={label}
                            description={description}
                            checked={Boolean(settings.notifications?.[key])}
                            onChange={(value) =>
                              toggleNotification(key, value)
                            }
                          />
                        ))}
                      </div>
                    </Card>
                  )}

                  {tab === "appearance" && (
                    <Card className="p-6">
                      <h3 className="text-base font-semibold text-white">
                        Appearance
                      </h3>
                      <p className="mt-1 text-sm text-neutral-400">
                        Personalise how Pkay AI looks.
                      </p>
                      <div className="mt-4 divide-y divide-white/5">
                        <div className="py-4">
                          <p className="text-sm font-medium text-white">
                            Theme
                          </p>
                          <p className="mt-0.5 text-xs text-neutral-500">
                            Applies to the dashboard immediately.
                          </p>
                          <div className="mt-3">
                            <Segmented
                              value={settings.theme}
                              onChange={setTheme}
                              options={[
                                { value: "dark", label: "Dark" },
                                { value: "light", label: "Light" },
                                { value: "system", label: "System" },
                              ]}
                            />
                          </div>
                        </div>
                        <div className="py-4">
                          <p className="text-sm font-medium text-white">
                            Density
                          </p>
                          <p className="mt-0.5 text-xs text-neutral-500">
                            Control spacing in the dashboard.
                          </p>
                          <div className="mt-3">
                            <Segmented
                              value={settings.density}
                              onChange={(value) =>
                                update({ density: value })
                              }
                              options={[
                                { value: "comfortable", label: "Comfortable" },
                                { value: "compact", label: "Compact" },
                              ]}
                            />
                          </div>
                        </div>
                      </div>
                    </Card>
                  )}

                  {tab === "api" && (
                    <Card className="p-6">
                      <h3 className="text-base font-semibold text-white">
                        API defaults
                      </h3>
                      <p className="mt-1 text-sm text-neutral-400">
                        Applied when a request omits these fields.
                      </p>
                      <div className="mt-6 grid gap-4 sm:grid-cols-2">
                        <SelectField
                          label="Default model"
                          value={settings.default_model}
                          onChange={(e) =>
                            update({ default_model: e.target.value })
                          }
                          options={MODELS.map((model) => ({
                            value: model.id,
                            label: model.name,
                          }))}
                        />
                        <SelectField
                          label="Default symbol"
                          value={settings.default_symbol}
                          onChange={(e) =>
                            update({ default_symbol: e.target.value })
                          }
                          options={[
                            "BTCUSDT",
                            "ETHUSDT",
                            "SOLUSDT",
                            "XAUUSD",
                          ].map((symbol) => ({
                            value: symbol,
                            label: symbol,
                          }))}
                        />
                        <SelectField
                          label="Default timeframe"
                          value={settings.default_timeframe}
                          onChange={(e) =>
                            update({ default_timeframe: e.target.value })
                          }
                          options={[
                            "1m",
                            "5m",
                            "15m",
                            "1h",
                            "4h",
                            "1d",
                            "1w",
                          ].map((timeframe) => ({
                            value: timeframe,
                            label: timeframe,
                          }))}
                        />
                      </div>
                    </Card>
                  )}

                  {tab === "security" && (
                    <Card className="p-6">
                      <h3 className="text-base font-semibold text-white">
                        Security
                      </h3>
                      <p className="mt-1 text-sm text-neutral-400">
                        Keep your account and keys safe.
                      </p>
                      <div className="mt-6 flex items-center justify-between border-t border-white/5 pt-4">
                        <div>
                          <p className="text-sm font-medium text-white">
                            Password
                          </p>
                          <p className="text-xs text-neutral-500">
                            Add or update your account password
                          </p>
                        </div>
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={() => setPasswordOpen(true)}
                        >
                          Change password
                        </Button>
                      </div>
                    </Card>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {passwordOpen && (
        <PasswordModal onClose={() => setPasswordOpen(false)} />
      )}
    </div>
  );
}
