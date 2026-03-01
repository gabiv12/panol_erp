/* static/js/app.js
   UI base (offline-first):
   - Theme toggle (claro/oscuro) con persistencia localStorage
   - Drawer sidebar mobile
   - Clock (data-clock)
   - Progress bars (data-progress + data-value)
   - Modales (dashboard)
   - Donuts (tortas) semáforo por módulo
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

  function toInt(v) {
    var n = parseInt(String(v || "0"), 10);
    return isNaN(n) ? 0 : n;
  }

  function clamp(n, a, b) {
    if (n < a) return a;
    if (n > b) return b;
    return n;
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
    return qs("[data-drawer]") || qs("#drawer");
  }

  function getOverlayEl() {
    return qs("[data-drawer-overlay]") || qs("#drawerOverlay");
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

  function initDrawer() {
    document.addEventListener("click", function (e) {
      var t = e.target;
      if (t && t.closest && t.closest("[data-drawer-open]")) {
        e.preventDefault();
        openDrawer();
        return;
      }
      if (t && t.closest && t.closest("[data-drawer-close]")) {
        e.preventDefault();
        closeDrawer();
        return;
      }
      if (t && (t.hasAttribute("data-drawer-overlay") || t.id === "drawerOverlay")) {
        e.preventDefault();
        closeDrawer();
        return;
      }
    }, true);

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        closeDrawer();
        closeAnyModal();
      }
    });
  }

  // ---------------------------
  // Clock (topbar)
  // ---------------------------
  function initClock() {
    var els = qsa("[data-clock]");
    if (!els.length) return;

    function pad(n) {
      return String(n).padStart(2, "0");
    }

    function tick() {
      var d = new Date();
      var s = pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
      els.forEach(function (el) {
        el.textContent = s;
      });
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
  // Modales
  // ---------------------------
  function openModalById(id) {
    var el = qs("#" + id);
    if (!el) return;
    el.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    el.setAttribute("aria-hidden", "false");
  }

  function closeModal(el) {
    if (!el) return;
    el.classList.add("hidden");
    el.setAttribute("aria-hidden", "true");
    document.body.classList.remove("overflow-hidden");
  }

  function closeAnyModal() {
    var open = qsa("[data-modal]").filter(function (m) {
      return !m.classList.contains("hidden");
    });
    if (!open.length) return;
    open.forEach(function (m) {
      closeModal(m);
    });
  }

  function initModals() {
    document.addEventListener("click", function (e) {
      var t = e.target;

      var openBtn = t && t.closest ? t.closest("[data-modal-open]") : null;
      if (openBtn) {
        e.preventDefault();
        var id = openBtn.getAttribute("data-modal-open");
        if (id) openModalById(id);
        return;
      }

      var closeBtn = t && t.closest ? t.closest("[data-modal-close]") : null;
      if (closeBtn) {
        e.preventDefault();
        var modal = closeBtn.closest("[data-modal]");
        closeModal(modal);
        return;
      }

      var overlay = t && t.closest ? t.closest("[data-modal-overlay]") : null;
      if (overlay) {
        e.preventDefault();
        var m2 = overlay.closest("[data-modal]");
        closeModal(m2);
        return;
      }
    }, true);
  }

  // ---------------------------
  // Donuts (tortas) semáforo
  // ---------------------------
  function donutStyle(ok, warn, bad, total) {
    ok = toInt(ok);
    warn = toInt(warn);
    bad = toInt(bad);
    total = toInt(total);

    if (total <= 0) {
      return { label: "--", bg: "conic-gradient(#94a3b8 0 100%)" };
    }

    // Ajustes para evitar desbordes (inventario puede traer bajo_min incluyendo sin_stock)
    if (ok + warn + bad > total) {
      // Regla: bad manda, warn se ajusta, ok es el resto
      var bad2 = clamp(bad, 0, total);
      var warn2 = clamp(warn - bad2, 0, total - bad2);
      var ok2 = clamp(total - bad2 - warn2, 0, total);
      ok = ok2;
      warn = warn2;
      bad = bad2;
    } else {
      // Si falta resto, va a "pendiente"
      // (no lo dibujamos como color aparte; se suma a warn para que no quede hueco)
      var rest = total - (ok + warn + bad);
      if (rest > 0) warn += rest;
    }

    var pOk = (ok / total) * 100;
    var pWarn = (warn / total) * 100;
    var pBad = (bad / total) * 100;

    var a = clamp(pOk, 0, 100);
    var b = clamp(a + pWarn, 0, 100);

    // Semáforo: verde / amarillo / rojo
    var bg = "conic-gradient(" +
      "#10b981 0% " + a.toFixed(2) + "%, " +
      "#f59e0b " + a.toFixed(2) + "% " + b.toFixed(2) + "%, " +
      "#ef4444 " + b.toFixed(2) + "% 100%)";

    var label = String(Math.round((ok / total) * 100)) + "%";
    return { label: label, bg: bg };
  }

  function renderDonuts() {
    var nodes = qsa("[data-donut]");
    if (!nodes.length) return;

    nodes.forEach(function (wrap) {
      var type = wrap.getAttribute("data-donut");
      var ring = qs("[data-donut-ring]", wrap);
      var label = qs("[data-donut-label]", wrap);
      if (!ring || !label) return;

      // Tipos especiales: VTV (se calcula con vencidos/hoy/porvencer/sinfecha)
      if (type === "vtv") {
        var total = toInt(wrap.getAttribute("data-total"));
        var vencidos = toInt(wrap.getAttribute("data-vencidos"));
        var hoy = toInt(wrap.getAttribute("data-hoy"));
        var por7 = toInt(wrap.getAttribute("data-porvencer7"));
        var sinfecha = toInt(wrap.getAttribute("data-sinfecha"));

        var bad = vencidos + hoy;
        var warn = por7 + sinfecha;
        var ok = total - bad - warn;
        if (ok < 0) ok = 0;

        var r1 = donutStyle(ok, warn, bad, total);
        ring.style.background = r1.bg;
        label.textContent = r1.label;
        return;
      }

      // Genérico: total/ok/warn/bad
      var total2 = toInt(wrap.getAttribute("data-total"));
      var ok2 = toInt(wrap.getAttribute("data-ok"));
      var warn2 = toInt(wrap.getAttribute("data-warn"));
      var bad2 = toInt(wrap.getAttribute("data-bad"));

      // Si ok no viene, lo infiere
      if (!wrap.hasAttribute("data-ok") && total2 > 0) {
        ok2 = total2 - warn2 - bad2;
        if (ok2 < 0) ok2 = 0;
      }

      var r2 = donutStyle(ok2, warn2, bad2, total2);
      ring.style.background = r2.bg;
      label.textContent = r2.label;
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
    initModals();
    renderDonuts();
  });
})();