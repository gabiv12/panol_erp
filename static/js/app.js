/* static/js/app.js
   UI base: drawer mobile + theme toggle + clock + progress bars
   - Robusto: soporta IDs (#drawer/#drawerOverlay) y data-attrs ([data-drawer], [data-drawer-overlay])
   - Robusto: listeners en capture + touchend (no lo rompe stopPropagation)
*/

(function () {
  "use strict";

  // ---------------------------
  // Helpers
  // ---------------------------
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  // ---------------------------
  // Theme (dark/light)
  // ---------------------------
  function getStoredTheme() {
    try {
      return localStorage.getItem("theme");
    } catch (e) {
      return null;
    }
  }

  function setStoredTheme(v) {
    try {
      localStorage.setItem("theme", v);
    } catch (e) {}
  }

  function applyTheme(theme) {
    var html = document.documentElement;
    var isDark = theme === "dark";
    html.classList.toggle("dark", isDark);

    var btn = qs("[data-theme-toggle]");
    if (btn) {
      btn.textContent = isDark ? "Oscuro" : "Claro";
      btn.setAttribute("aria-pressed", isDark ? "true" : "false");
    }
  }

  function initThemeToggle() {
    var stored = getStoredTheme();
    if (!stored) {
      stored = document.documentElement.classList.contains("dark") ? "dark" : "light";
      setStoredTheme(stored);
    }
    applyTheme(stored);

    var btn = qs("[data-theme-toggle]");
    if (!btn) return;

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var current = getStoredTheme() || "light";
      var next = current === "dark" ? "light" : "dark";
      setStoredTheme(next);
      applyTheme(next);
    });
  }

  // ---------------------------
  // Drawer (mobile sidebar)
  // ---------------------------
  function getDrawerEl() {
    return (
      qs("[data-drawer]") ||
      qs("#drawer") ||
      qs("#tiDrawer")
    );
  }

  function getOverlayEl() {
    return (
      qs("[data-drawer-overlay]") ||
      qs("#drawerOverlay") ||
      qs("#tiOverlay")
    );
  }

  function openDrawer() {
    var drawer = getDrawerEl();
    var overlay = getOverlayEl();
    if (!drawer || !overlay) return;

    drawer.classList.remove("hidden");
    overlay.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  function closeDrawer() {
    var drawer = getDrawerEl();
    var overlay = getOverlayEl();
    if (!drawer || !overlay) return;

    drawer.classList.add("hidden");
    overlay.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  function isOpenBtn(target) {
    return !!(target && target.closest && target.closest("[data-drawer-open]"));
  }

  function isCloseBtn(target) {
    return !!(target && target.closest && target.closest("[data-drawer-close]"));
  }

  function isOverlay(target) {
    if (!target) return false;
    if (target.hasAttribute && target.hasAttribute("data-drawer-overlay")) return true;
    if (target.id === "drawerOverlay" || target.id === "tiOverlay") return true;
    return false;
  }

  function initDrawer() {
    // Capture: no lo rompe stopPropagation de otros scripts
    function handler(e) {
      var t = e.target;
      if (isOpenBtn(t)) {
        e.preventDefault();
        openDrawer();
        return;
      }
      if (isCloseBtn(t) || isOverlay(t)) {
        e.preventDefault();
        closeDrawer();
        return;
      }
    }

    document.addEventListener("click", handler, true);
    document.addEventListener("touchend", handler, true);

    // Escape cierra
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeDrawer();
    });
  }

  // ---------------------------
  // Clock (topbar)
  // ---------------------------
  function initClock() {
    var el = qs("[data-clock]");
    if (!el) return;

    function pad(n) {
      return String(n).padStart(2, "0");
    }

    function tick() {
      var d = new Date();
      el.textContent = pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
    }

    tick();
    setInterval(tick, 1000);
  }

  // ---------------------------
  // Progress bars
  // ---------------------------
  function initProgress() {
    var els = qsa("[data-progress][data-value]");
    if (!els.length) return;

    els.forEach(function (el) {
      var v = parseFloat(el.getAttribute("data-value") || "0");
      if (isNaN(v)) v = 0;
      if (v < 0) v = 0;
      if (v > 100) v = 100;
      el.style.width = v + "%";
    });
  }

  // ---------------------------
  // Boot
  // ---------------------------
  document.addEventListener("DOMContentLoaded", function () {
    initThemeToggle();
    initDrawer();
    initClock();
    initProgress();
  });
})();