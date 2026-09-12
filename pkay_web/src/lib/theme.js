const THEME_KEY = "pkay.theme";

export function resolveTheme(theme) {
  if (theme === "system") {
    try {
      return window.matchMedia("(prefers-color-scheme: light)").matches
        ? "light"
        : "dark";
    } catch {
      return "dark";
    }
  }
  return theme === "light" ? "light" : "dark";
}

export function loadTheme() {
  try {
    return localStorage.getItem(THEME_KEY) || "dark";
  } catch {
    return "dark";
  }
}

export function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* ignore */
  }
}

export function applyTheme(theme) {
  saveTheme(theme);
  const resolved = resolveTheme(theme);
  document.documentElement.dataset.theme = resolved;
}
