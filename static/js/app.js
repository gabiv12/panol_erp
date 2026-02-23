/* static/js/app.js
   Pañol ERP - UI Core (layout)
   - Drawer mobile (sidebar)
   - Toggle tema (claro/oscuro) con persistencia
   - Helpers pequeños (clock en topbar, toggle password por data-attrs)

   Reglas del proyecto:
   - NO inline JS en templates
   - Este archivo solo maneja UI base. Lo específico de cada vista va en static/js/pages/...
*/

(function () {
  "use strict";

  // =====================
  // Theme
  // =====================
  function getStoredTheme() {
    return localStorage.getItem("theme"); // "dark" | "light" | null
  }

  function prefersDark() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function isDarkActive() {
    const stored = getStoredTheme();
    if (stored === "dark") return true;
    if (stored === "light") return false;
    return prefersDark();
  }

  function applyTheme(isDark) {
    document.documentElement.classList.toggle("dark", !!isDark);
  }

  function setThemeStored(isDark) {
    localStorage.setItem("theme", isDark ? "dark" : "light");
  }

  function refreshThemeButton() {
    const icon = document.querySelector("[data-theme-icon]");
    const text = document.querySelector("[data-theme-text]");
    if (!icon || !text) return;

    const dark = document.documentElement.classList.contains("dark");
    icon.textContent = dark ? "☀" : "☾";
    text.textContent = dark ? "Claro" : "Oscuro";
  }

  function initTheme() {
    applyTheme(isDarkActive());
    refreshThemeButton();

    document.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-theme-toggle]");
      if (!btn) return;

      const dark = !document.documentElement.classList.contains("dark");
      applyTheme(dark);
      setThemeStored(dark);
      refreshThemeButton();
    });
  }

  // =====================
  // Drawer (mobile sidebar)
  // =====================
  const drawer = () => document.getElementById("tiDrawer");
  const overlay = () => document.getElementById("tiOverlay");

  function openDrawer() {
    const d = drawer();
    const o = overlay();
    if (!d || !o) return;

    d.classList.remove("-translate-x-full");
    o.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  function closeDrawer() {
    const d = drawer();
    const o = overlay();
    if (!d || !o) return;

    d.classList.add("-translate-x-full");
    o.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  function initDrawer() {
    document.addEventListener("click", (ev) => {
      if (ev.target.closest("[data-drawer-open]")) {
        openDrawer();
        return;
      }
      if (ev.target.closest("[data-drawer-close]")) {
        closeDrawer();
        return;
      }
      if (ev.target === overlay()) {
        closeDrawer();
      }
    });

    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") closeDrawer();
    });
  }

  // =====================
  // Clock (optional)
  // =====================
  function initClock() {
    const el = document.querySelector("[data-clock]");
    if (!el) return;

    function tick() {
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      const ss = String(now.getSeconds()).padStart(2, "0");
      el.textContent = `${hh}:${mm}:${ss}`;
    }

    tick();
    window.setInterval(tick, 1000);
  }

  // =====================
  // Password toggle (data-toggle-password)
  // =====================
  function initPasswordToggles() {
    document.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-toggle-password]");
      if (!btn) return;

      const target = btn.getAttribute("data-target");
      if (!target) return;

      const input = document.querySelector(target);
      if (!input) return;

      const isPassword = input.getAttribute("type") === "password";
      input.setAttribute("type", isPassword ? "text" : "password");
      btn.textContent = isPassword ? "Ocultar" : "Mostrar";
    });
  }

  // Boot
  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    initDrawer();
    initClock();
    initPasswordToggles();
  });
})();
