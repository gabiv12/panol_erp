// inventario/static/inventario/js/movimientos.js
// UI mínima para MovimientoStockForm:
// - muestra/oculta "Ubicación destino" cuando tipo = TRANSFERENCIA

(function () {
  'use strict';

  function $(id) {
    return document.getElementById(id);
  }

  function setDestinoVisibility() {
    const tipo = $('id_tipo');
    const wrap = $('destino_wrap');
    const destino = $('id_ubicacion_destino');
    if (!tipo || !wrap || !destino) return;

    const isTransfer = String(tipo.value || '').toUpperCase() === 'TRANSFERENCIA';

    if (isTransfer) {
      wrap.classList.remove('hidden');
      destino.removeAttribute('disabled');
      // visualmente requerido (la validación real está en backend)
      destino.setAttribute('required', 'required');
    } else {
      wrap.classList.add('hidden');
      destino.setAttribute('disabled', 'disabled');
      destino.removeAttribute('required');
      destino.value = '';
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    const tipo = $('id_tipo');
    if (tipo) {
      tipo.addEventListener('change', setDestinoVisibility);
    }
    setDestinoVisibility();
  });
})();
