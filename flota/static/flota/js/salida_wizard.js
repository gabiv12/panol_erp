/*
flota/static/flota/js/salida_wizard.js

Wizard simple de 3 pasos para cargar Salidas programadas.

Objetivo:
- Reducir errores y carga mental del diagramador.
- Permitir que una persona "no experta" pueda completar el formulario guiada.

Reglas:
- No se deshabilita ningún input al submit (evitamos que no se envíen valores).
- El botón Guardar solo se muestra en el paso final (pero el de arriba siempre está disponible).
*/

(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  const form = qs("#salidaForm");
  if (!form) return;

  const steps = qsa("[data-step]", form);
  const stepBtns = qsa("[data-step-btn]", form);
  const lbl = qs("#stepLabel", form);

  const btnNexts = qsa("[data-next-step]", form);
  const btnPrevs = qsa("[data-prev-step]", form);

  let current = 1;

  function setActiveStep(n) {
    current = Math.max(1, Math.min(3, n));
    steps.forEach((el) => {
      const sn = parseInt(el.getAttribute("data-step"), 10);
      if (sn === current) el.classList.remove("hidden");
      else el.classList.add("hidden");
    });

    stepBtns.forEach((b) => {
      const sn = parseInt(b.getAttribute("data-step-btn"), 10);
      if (sn === current) b.classList.add("ti-btn-primary");
      else b.classList.remove("ti-btn-primary");
    });

    if (lbl) lbl.textContent = `Paso ${current}/3`;
  }

  stepBtns.forEach((b) => {
    b.addEventListener("click", () => setActiveStep(parseInt(b.getAttribute("data-step-btn"), 10)));
  });

  btnNexts.forEach((b) => b.addEventListener("click", () => setActiveStep(current + 1)));
  btnPrevs.forEach((b) => b.addEventListener("click", () => setActiveStep(current - 1)));

  setActiveStep(1);

  // ------------------------------------------------------------------
  // Info del colectivo (alerta por partes abiertos)
  // ------------------------------------------------------------------
  const url = form.getAttribute("data-colectivo-info-url");
  const selColectivo = qs("#id_colectivo", form);
  const infoBox = qs("#colectivoInfo", form);
  const infoTitle = qs("#colectivoInfoTitle", form);
  const infoSub = qs("#colectivoInfoSub", form);
  const infoBadge = qs("#colectivoInfoBadge", form);
  const infoMsg = qs("#colectivoInfoMsg", form);
  const infoLast = qs("#colectivoInfoLast", form);

  async function refreshInfo() {
    if (!url || !selColectivo || !infoBox) return;
    const id = selColectivo.value;
    if (!id) {
      infoBox.classList.add("hidden");
      return;
    }

    try {
      const resp = await fetch(`${url}?colectivo_id=${encodeURIComponent(id)}`, { credentials: "same-origin" });
      const data = await resp.json();
      if (!data.ok) throw new Error(data.error || "Error");

      infoBox.classList.remove("hidden");

      const c = data.colectivo || {};
      const p = data.partes || {};
      const abiertos = Number(p.abiertos || 0);

      if (infoTitle) infoTitle.textContent = `Interno ${c.interno} · ${c.dominio}`;
      if (infoSub) infoSub.textContent = abiertos > 0 ? "Atención: hay partes pendientes" : "Sin partes pendientes";
      if (infoBadge) infoBadge.textContent = abiertos > 0 ? `Partes: ${abiertos}` : "OK";

      if (infoMsg) {
        if (abiertos > 0) {
          infoMsg.textContent = "Podés usar esta unidad igual, pero conviene revisar los partes antes de confirmarla.";
        } else {
          infoMsg.textContent = "Unidad sin alertas de partes.";
        }
      }

      if (infoLast) {
        if (p.ultimo) {
          infoLast.textContent = `Último parte abierto: ${p.ultimo.severidad} · ${p.ultimo.estado} · ${p.ultimo.resumen}`;
        } else {
          infoLast.textContent = "";
        }
      }
    } catch (e) {
      infoBox.classList.remove("hidden");
      if (infoTitle) infoTitle.textContent = "Unidad";
      if (infoSub) infoSub.textContent = "No se pudo obtener info";
      if (infoBadge) infoBadge.textContent = "—";
      if (infoMsg) infoMsg.textContent = "Reintentá seleccionando la unidad de nuevo.";
      if (infoLast) infoLast.textContent = "";
    }
  }

  if (selColectivo) {
    selColectivo.addEventListener("change", refreshInfo);
    setTimeout(refreshInfo, 200);
  }
})();
