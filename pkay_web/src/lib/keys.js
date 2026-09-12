const STORAGE_KEY = "pkay.api_keys.v1";

function randomToken(length = 32) {
  const alphabet =
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  const bytes = new Uint8Array(length);
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < length; i += 1) {
      bytes[i] = Math.floor(Math.random() * 256);
    }
  }
  return Array.from(bytes, (b) => alphabet[b % alphabet.length]).join("");
}

export function generateKey(environment = "live") {
  return `pk_${environment}_${randomToken(32)}`;
}

export function maskKey(key) {
  if (!key || key.length < 12) return key;
  return `${key.slice(0, 12)}${"•".repeat(12)}${key.slice(-4)}`;
}

export function loadKeys() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persist(keys) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
  window.dispatchEvent(new CustomEvent("pkay:keys-changed"));
}

export function createKey({ name, environment = "live", scopes = [] }) {
  const keys = loadKeys();
  const key = {
    id: `key_${Date.now()}_${Math.floor(Math.random() * 1e6)}`,
    name: name?.trim() || "Untitled key",
    environment,
    scopes,
    secret: generateKey(environment),
    prefix: "",
    createdAt: new Date().toISOString(),
    lastUsedAt: null,
    requests: 0,
    status: "active",
  };
  key.prefix = key.secret.slice(0, 12);
  const next = [key, ...keys];
  persist(next);
  return key;
}

export function revokeKey(id) {
  const next = loadKeys().map((k) =>
    k.id === id ? { ...k, status: "revoked", secret: "" } : k
  );
  persist(next);
  return next;
}

export function deleteKey(id) {
  const next = loadKeys().filter((k) => k.id !== id);
  persist(next);
  return next;
}
