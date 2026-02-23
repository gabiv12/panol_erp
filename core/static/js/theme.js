(function () {
  const KEY = "theme"; // "dark" | "light"

  function applyTheme(mode) {
    const root = document.documentElement;
    if (mode === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
  }

  function getPreferred() {
    const saved = localStorage.getItem(KEY);
    if (saved === "dark" || saved === "light") return saved;
    // fallback a preferencia del sistema
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function toggleTheme() {
    const root = document.documentElement;
    const next = root.classList.contains("dark") ? "light" : "dark";
    localStorage.setItem(KEY, next);
    applyTheme(next);
  }

  // Init
  applyTheme(getPreferred());

  // Bind
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
      btn.addEventListener("click", toggleTheme);
    });
  });

  // opcional: exponer para debug
  window.__toggleTheme = toggleTheme;
})();