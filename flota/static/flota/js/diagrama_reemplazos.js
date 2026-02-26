(function () {
  const occupiedIds = (window.__OCCUPIED_IDS__ || []);
  if (!occupiedIds.length) return;

  const occupiedSet = new Set(occupiedIds.map(String));

  document.querySelectorAll('select[name$="-colectivo"]').forEach(function (sel) {
    const current = String(sel.value || "");
    Array.from(sel.options).forEach(function (opt) {
      const v = String(opt.value || "");
      if (!v) return;
      if (occupiedSet.has(v) && v !== current) {
        opt.disabled = true;
      }
    });
  });
})();
