// flota/js/colectivos.js
// Listado de Colectivos (Flota)
// - Confirmación de eliminado (sin romper navegación)
// - Pequeñas mejoras UX para filtros (futuro)

(() => {
  "use strict";

  // Confirmación simple al eliminar (si existe el link "Eliminar")
  document.addEventListener("click", (ev) => {
    const a = ev.target.closest('a[href*="/eliminar/"]');
    if (!a) return;
    const ok = confirm("¿Eliminar este colectivo? Esta acción no se puede deshacer.");
    if (!ok) ev.preventDefault();
  });
})();
