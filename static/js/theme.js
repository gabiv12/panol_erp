(function () {
  const root = document.documentElement;
  const storageKey = "theme";

  function preferredTheme() {
    const saved = localStorage.getItem(storageKey);
    if (saved === "dark" || saved === "light") return saved;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    if (theme === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
  }

  function updateButton(btn) {
    if (!btn) return;
    const isDark = root.classList.contains("dark");
    btn.textContent = isDark ? "Claro" : "Oscuro";
    btn.setAttribute("aria-pressed", isDark ? "true" : "false");
  }

  // aplicar apenas carga (antes de que pinte la UI)
  applyTheme(preferredTheme());

  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("themeToggle");
    updateButton(btn);

    if (!btn) return;

    btn.addEventListener("click", function () {
      const isDark = root.classList.contains("dark");
      const next = isDark ? "light" : "dark";
      localStorage.setItem(storageKey, next);
      applyTheme(next);
      updateButton(btn);
    });
  });
})();
