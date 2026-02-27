
  // ---------------------------
  // Internal modal (no browser alert/confirm)
  // ---------------------------
  function ensureModal() {
    var existing = qs("#tiModalOverlay");
    if (existing) return existing;

    var overlay = document.createElement("div");
    overlay.id = "tiModalOverlay";
    overlay.className = "fixed inset-0 z-[9999] hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4";

    var panel = document.createElement("div");
    panel.id = "tiModalPanel";
    panel.className = "w-full max-w-lg ti-card p-4";

    var title = document.createElement("div");
    title.id = "tiModalTitle";
    title.className = "text-base font-semibold mb-2";
    title.textContent = "Confirmar";

    var msg = document.createElement("div");
    msg.id = "tiModalMsg";
    msg.className = "text-sm ti-muted whitespace-pre-wrap";

    var actions = document.createElement("div");
    actions.className = "mt-4 flex items-center justify-end gap-2";

    var cancel = document.createElement("button");
    cancel.type = "button";
    cancel.id = "tiModalCancel";
    cancel.className = "ti-btn";
    cancel.textContent = "Cancelar";

    var ok = document.createElement("button");
    ok.type = "button";
    ok.id = "tiModalOk";
    ok.className = "ti-btn-primary";
    ok.textContent = "Aceptar";

    actions.appendChild(cancel);
    actions.appendChild(ok);

    panel.appendChild(title);
    panel.appendChild(msg);
    panel.appendChild(actions);

    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    return overlay;
  }

  function showModal(opts) {
    var overlay = ensureModal();
    var titleEl = qs("#tiModalTitle", overlay);
    var msgEl = qs("#tiModalMsg", overlay);
    var btnOk = qs("#tiModalOk", overlay);
    var btnCancel = qs("#tiModalCancel", overlay);

    titleEl.textContent = (opts && opts.title) ? opts.title : "Confirmar";
    msgEl.textContent = (opts && opts.message) ? opts.message : "";

    btnOk.textContent = (opts && opts.okText) ? opts.okText : "Aceptar";
    btnCancel.textContent = (opts && opts.cancelText) ? opts.cancelText : "Cancelar";

    var mode = (opts && opts.mode) ? opts.mode : "confirm"; // confirm|alert
    btnCancel.classList.toggle("hidden", mode === "alert");

    overlay.classList.remove("hidden");

    function close() { overlay.classList.add("hidden"); cleanup(); }
    function cleanup() {
      overlay.removeEventListener("click", onOverlayClick, true);
      document.removeEventListener("keydown", onKey, true);
      btnOk.removeEventListener("click", onOk, true);
      btnCancel.removeEventListener("click", onCancel, true);
    }
    function onOverlayClick(e) {
      if (e.target === overlay) {
        if (mode === "alert") { onOk(e); }
        else { onCancel(e); }
      }
    }
    function onKey(e) {
      if (e.key === "Escape") {
        if (mode === "alert") { onOk(e); }
        else { onCancel(e); }
      }
    }

    var resolver = (opts && opts.resolve) ? opts.resolve : function(){};
    function onOk(e) { e && e.preventDefault(); close(); resolver(true); }
    function onCancel(e) { e && e.preventDefault(); close(); resolver(false); }

    overlay.addEventListener("click", onOverlayClick, true);
    document.addEventListener("keydown", onKey, true);
    btnOk.addEventListener("click", onOk, true);
    btnCancel.addEventListener("click", onCancel, true);

    setTimeout(function(){ btnOk.focus(); }, 0);
  }

  window.tiAlert = function(message, title) {
    return new Promise(function(resolve){
      showModal({mode:"alert", title: title || "Aviso", message: String(message || ""), okText:"Aceptar", resolve: function(){ resolve(true); }});
    });
  };

  window.tiConfirm = function(message, title) {
    return new Promise(function(resolve){
      showModal({mode:"confirm", title: title || "Confirmar", message: String(message || ""), okText:"Aceptar", cancelText:"Cancelar", resolve: resolve});
    });
  };
﻿/* static/js/app.js
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