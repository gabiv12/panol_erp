// static/js/pages/usuarios/usuarios.js
// Usuarios - UI helpers (sin frameworks)
// Objetivo:
// - Evitar clicks “muertos”: la fila se puede abrir para editar (click en la fila).
// - Confirmar antes de eliminar (evita borrados accidentales).
//
// Reglas:
// - NO JS inline en templates.
// - Este JS solo afecta a /usuarios/ (usuario_list.html).

(function () {
  'use strict';

  function isInteractive(el) {
    return !!(el && el.closest('a,button,input,select,textarea,label'));
  }

  function initRowClickToEdit() {
    const table = document.querySelector('table');
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr');
    rows.forEach((tr) => {
      const editLink = tr.querySelector('a[href*="/editar/"]');
      if (!editLink) return;

      tr.style.cursor = 'pointer';
      tr.addEventListener('click', (ev) => {
        if (isInteractive(ev.target)) return;
        window.location.href = editLink.href;
      });
    });
  }

  function initDeleteConfirm() {
    const links = document.querySelectorAll('a[href*="/eliminar/"]');
    links.forEach((a) => {
      a.addEventListener('click', (ev) => {
        const userMsg = (a.getAttribute('data-confirm') || '').trim();
        const msg = userMsg || '¿Eliminar este registro? Esta acción no se puede deshacer.';
        if (!window.confirm(msg)) ev.preventDefault();
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initRowClickToEdit();
    initDeleteConfirm();
  });
})();
