const API_URL = (
  import.meta.env.VITE_API_URL || "https://auth.pkay.fun"
).replace(/\/$/, "");

const TOKEN_KEY = "pkay.token";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.error) message = body.error;
    } catch {
      /* ignore */
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}

export const authUrl = `${API_URL}/api/v3/auth/google`;

export const api = {
  baseUrl: API_URL,
  getToken,
  setToken,
  clearToken,
  isSignedIn: () => Boolean(getToken()),
  me: () => request("/api/v3/auth/me"),
  listKeys: () => request("/api/v3/keys"),
  createKey: (payload) =>
    request("/api/v3/keys", { method: "POST", body: JSON.stringify(payload) }),
  revokeKey: (id) =>
    request(`/api/v3/keys/${id}/revoke`, { method: "POST" }),
  deleteKey: (id) => request(`/api/v3/keys/${id}`, { method: "DELETE" }),
  usage: (days = 14) => request(`/api/v3/usage?days=${days}`),
  getSettings: () => request("/api/v3/settings"),
  updateSettings: (payload) =>
    request("/api/v3/settings", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  changePassword: (payload) =>
    request("/api/v3/auth/password", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyze: (payload) =>
    request("/api/v3/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
