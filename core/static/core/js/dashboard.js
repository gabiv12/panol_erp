// static/js/pages/dashboard.js
// Dashboard (Etapa 2) - lógica mínima de UI (sin frameworks)
// - Setea barras de progreso desde data-value (evita inline style en templates)

(function () {
  'use strict';

  function clamp(n, min, max) {
    if (Number.isNaN(n)) return min;
    return Math.min(max, Math.max(min, n));
  }

  function initProgressBars() {
    const bars = document.querySelectorAll('[data-progress][data-value]');
    bars.forEach((bar) => {
      const raw = String(bar.getAttribute('data-value') || '0').trim();
      const val = clamp(parseFloat(raw), 0, 100);
      bar.style.width = val + '%';
      bar.setAttribute('aria-valuenow', String(val));
      bar.setAttribute('role', 'progressbar');
      bar.setAttribute('aria-valuemin', '0');
      bar.setAttribute('aria-valuemax', '100');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initProgressBars();
  });
})();
