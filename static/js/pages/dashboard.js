/* static/js/pages/dashboard.js
   - Setea barras de progreso del dashboard.
   - No depende de librerías.
*/
(function () {
  "use strict";

  function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
  }

  function initProgressBars() {
    document.querySelectorAll("[data-progress][data-value]").forEach((el) => {
      const raw = el.getAttribute("data-value");
      let v = Number(raw);
      if (!Number.isFinite(v)) v = 0;
      v = clamp(v, 0, 100);
      el.style.width = v + "%";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initProgressBars();
  });
})();