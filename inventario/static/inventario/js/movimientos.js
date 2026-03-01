// inventario/static/inventario/js/movimientos.js
// UX Nivel 2 (MovimientoStock) + stock por ubicación (EGRESO/TRANSFERENCIA)

(function () {
  "use strict";

  const LS_KEY = "lt_inv_last_products_v2";
  const LS_MAX = 5;

  function $(id) {
    return document.getElementById(id);
  }

  function safeStr(v) {
    return String(v || "").trim();
  }

  function norm(v) {
    return safeStr(v)
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function upper(v) {
    return safeStr(v).toUpperCase();
  }

  function toNum(v) {
    const raw = safeStr(v).replace(",", ".");
    const n = raw ? Number(raw) : 0;
    return Number.isFinite(n) ? n : 0;
  }

  function fmtQty(n) {
    if (n === null || n === undefined) return "—";
    const x = Number(n);
    if (!Number.isFinite(x)) return "—";
    if (Math.abs(x - Math.round(x)) < 1e-9) return String(Math.round(x));
    return x.toFixed(2);
  }

  function getTipoSelect() {
    return $("id_tipo");
  }

  function buildTipoMap() {
    const sel = getTipoSelect();
    const map = {
      INGRESO: null,
      EGRESO: null,
      AJUSTE: null,
      TRANSFERENCIA: null,
    };
    if (!sel) return map;

    const opts = Array.from(sel.options || []);
    opts.forEach((o) => {
      const v = upper(o.value);
      const t = norm(o.textContent);

      if (v === "INGRESO") map.INGRESO = o.value;
      if (v === "EGRESO") map.EGRESO = o.value;
      if (v === "AJUSTE") map.AJUSTE = o.value;
      if (v === "TRANSFERENCIA") map.TRANSFERENCIA = o.value;

      if (!map.INGRESO && (t.includes("ingreso") || t.includes("entrada"))) map.INGRESO = o.value;
      if (!map.EGRESO && (t.includes("egreso") || t.includes("salida"))) map.EGRESO = o.value;
      if (!map.AJUSTE && t.includes("ajuste")) map.AJUSTE = o.value;
      if (!map.TRANSFERENCIA && t.includes("transfer")) map.TRANSFERENCIA = o.value;
    });

    return map;
  }

  function keyFromSelect(map) {
    const sel = getTipoSelect();
    if (!sel) return "";

    const v = sel.value;
    if (map.INGRESO !== null && v === map.INGRESO) return "INGRESO";
    if (map.EGRESO !== null && v === map.EGRESO) return "EGRESO";
    if (map.AJUSTE !== null && v === map.AJUSTE) return "AJUSTE";
    if (map.TRANSFERENCIA !== null && v === map.TRANSFERENCIA) return "TRANSFERENCIA";

    const opt = sel.options[sel.selectedIndex];
    const t = norm(opt ? opt.textContent : "");
    if (t.includes("ingreso") || t.includes("entrada")) return "INGRESO";
    if (t.includes("egreso") || t.includes("salida")) return "EGRESO";
    if (t.includes("ajuste")) return "AJUSTE";
    if (t.includes("transfer")) return "TRANSFERENCIA";
    return "";
  }

  function setTipoByKey(key, map) {
    const sel = getTipoSelect();
    if (!sel) return;

    let val = null;
    if (key === "INGRESO") val = map.INGRESO;
    if (key === "EGRESO") val = map.EGRESO;
    if (key === "AJUSTE") val = map.AJUSTE;
    if (key === "TRANSFERENCIA") val = map.TRANSFERENCIA;
    if (val === null) val = key;

    sel.disabled = false;
    sel.value = val;
    sel.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function setDestinoVisibility(tipoKey) {
    const wrap = $("destino_wrap");
    const destino = $("id_ubicacion_destino");
    if (!wrap || !destino) return;

    const isTransfer = tipoKey === "TRANSFERENCIA";
    if (isTransfer) {
      wrap.classList.remove("hidden");
      destino.disabled = false;
      destino.setAttribute("required", "required");
    } else {
      wrap.classList.add("hidden");
      destino.disabled = true;
      destino.removeAttribute("required");
      destino.value = "";
    }
  }

  function toggleOptionalByTipo(tipoKey) {
    const proveedorWrap = $("proveedor_wrap");
    const loteWrap = $("lote_wrap");
    const vencWrap = $("venc_wrap");
    const observWrap = $("observ_wrap");
    const tipoHint = $("tipo_hint");

    if (proveedorWrap) proveedorWrap.classList.remove("hidden");
    if (loteWrap) loteWrap.classList.remove("hidden");
    if (vencWrap) vencWrap.classList.remove("hidden");
    if (observWrap) observWrap.classList.remove("hidden");

    if (tipoHint) {
      if (tipoKey === "INGRESO") tipoHint.textContent = "Entrada: ingresa stock al pañol.";
      else if (tipoKey === "EGRESO") tipoHint.textContent = "Salida: usa stock del pañol (requiere stock disponible).";
      else if (tipoKey === "AJUSTE") tipoHint.textContent = "Ajuste: corrige stock (sumá/restá). Recomendado: explicar el motivo.";
      else if (tipoKey === "TRANSFERENCIA") tipoHint.textContent = "Transferencia: mueve stock entre ubicaciones (origen → destino).";
      else tipoHint.textContent = "Elegí una acción para que el formulario se acomode.";
    }

    if (tipoKey === "EGRESO") {
      if (proveedorWrap) proveedorWrap.classList.add("hidden");
    }

    if (tipoKey === "TRANSFERENCIA") {
      if (proveedorWrap) proveedorWrap.classList.add("hidden");
    }
  }

  function setPillsActive(tipoKey) {
    const pills = document.querySelectorAll("#tipo_pills [data-tipo]");
    pills.forEach((btn) => {
      const v = upper(btn.getAttribute("data-tipo"));
      const isActive = v === tipoKey;
      btn.classList.toggle("ti-btn-primary", isActive);
      btn.classList.toggle("ti-btn", !isActive);
      btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function loadLastProducts() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      const arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
    }
  }

  function saveLastProduct(id, label) {
    if (!id) return;
    const arr = loadLastProducts().filter((x) => x && String(x.id) !== String(id));
    arr.unshift({ id: String(id), label: String(label || id) });
    const trimmed = arr.slice(0, LS_MAX);
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(trimmed));
    } catch (e) {}
  }

  function renderLastProducts() {
    const box = $("producto_recientes");
    const sel = $("id_producto");
    if (!box || !sel) return;

    const arr = loadLastProducts();
    box.innerHTML = "";
    if (!arr.length) return;

    const title = document.createElement("div");
    title.className = "text-xs ti-subtitle w-full";
    title.textContent = "Recientes:";
    box.appendChild(title);

    arr.forEach((it) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "ti-btn px-3 py-1 text-xs";
      b.textContent = it.label;
      b.addEventListener("click", function () {
        sel.value = it.id;
        sel.dispatchEvent(new Event("change", { bubbles: true }));
      });
      box.appendChild(b);
    });
  }

  // ✅ Optimizado: precomputo normalizado + debounce + DocumentFragment
  function initProductSearch() {
    const search = $("producto_search");
    const sel = $("id_producto");
    if (!search || !sel) return;

    const options = Array.from(sel.options || []);
    if (!options.length) return;

    const cache = options.map((o, idx) => ({
      value: String(o.value),
      text: String(o.textContent),
      nValue: norm(o.value),
      nText: norm(o.textContent),
      isPlaceholder: idx === 0,
    }));

    let timer = null;

    function applyFilter() {
      const q = norm(search.value);
      const current = sel.value;

      const frag = document.createDocumentFragment();

      cache.forEach((it) => {
        if (it.isPlaceholder) {
          const o = document.createElement("option");
          o.value = it.value;
          o.textContent = it.text;
          frag.appendChild(o);
          return;
        }

        if (!q || it.nText.includes(q) || it.nValue.includes(q)) {
          const o = document.createElement("option");
          o.value = it.value;
          o.textContent = it.text;
          frag.appendChild(o);
        }
      });

      sel.innerHTML = "";
      sel.appendChild(frag);

      if (current) {
        const exists = Array.from(sel.options).some((o) => String(o.value) === String(current));
        if (exists) sel.value = current;
      }
    }

    search.addEventListener("input", function () {
      if (timer) clearTimeout(timer);
      timer = setTimeout(applyFilter, 120);
    });

    applyFilter();
  }

  function focusCantidad() {
    const cant = $("id_cantidad");
    if (cant) cant.focus();
  }

  function getStockUrl() {
    const el = document.querySelector("[data-stock-url]");
    return el ? el.getAttribute("data-stock-url") : "";
  }

  const STOCK_CACHE = new Map();

  // ✅ Para evitar UI “pisada” por respuestas viejas
  let refreshSeq = 0;
  let stockAbort = null;

  function fetchStock(productoId, signal) {
    const url = getStockUrl();
    if (!url || !productoId) return Promise.resolve({ map: new Map(), list: [] });

    const key = String(productoId);
    if (STOCK_CACHE.has(key)) return Promise.resolve(STOCK_CACHE.get(key));

    return fetch(url + "?producto_id=" + encodeURIComponent(productoId), {
      method: "GET",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
      signal,
    })
      .then((r) => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then((data) => {
        const list = data && data.ok && Array.isArray(data.stocks) ? data.stocks : [];
        const m = new Map();
        list.forEach((it) => {
          m.set(String(it.ubicacion_id), Number(it.cantidad || 0));
        });
        const pack = { map: m, list };
        STOCK_CACHE.set(key, pack);
        return pack;
      })
      .catch(() => ({ map: new Map(), list: [] }));
  }

  function buildSelectCache(sel) {
    return Array.from(sel.options || []).map((o) => ({ value: String(o.value), text: String(o.textContent) }));
  }

  function rebuildSelectFromCache(sel, cache, selectedValue) {
    const frag = document.createDocumentFragment();
    cache.forEach((it) => {
      const opt = document.createElement("option");
      opt.value = it.value;
      opt.textContent = it.text;
      frag.appendChild(opt);
    });
    sel.innerHTML = "";
    sel.appendChild(frag);

    if (selectedValue) {
      const exists = Array.from(sel.options).some((o) => String(o.value) === String(selectedValue));
      if (exists) sel.value = selectedValue;
    }
  }

  function applyOrigenFilter(tipoKey, productoId, stockPack, ubicAllCache, ubicLabelMap) {
    const selUbic = $("id_ubicacion");
    if (!selUbic) return;

    const mustHaveStock = tipoKey === "EGRESO" || tipoKey === "TRANSFERENCIA";
    const prev = selUbic.value;

    if (!mustHaveStock || !productoId) {
      rebuildSelectFromCache(selUbic, ubicAllCache, prev);
      selUbic.disabled = false;
      return;
    }

    const list = stockPack && Array.isArray(stockPack.list) ? stockPack.list : [];
    const withStock = list.filter((it) => Number(it.cantidad || 0) > 0);

    const frag = document.createDocumentFragment();

    const ph = ubicAllCache && ubicAllCache.length ? ubicAllCache[0] : { value: "", text: "—" };
    const o0 = document.createElement("option");
    o0.value = ph.value;
    o0.textContent = ph.text;
    frag.appendChild(o0);

    withStock.forEach((it) => {
      const id = String(it.ubicacion_id);
      const qty = Number(it.cantidad || 0);
      const baseLabel = (ubicLabelMap && ubicLabelMap.get(id)) || String(it.ubicacion || id);
      const opt = document.createElement("option");
      opt.value = id;
      opt.textContent = baseLabel + " · Stock: " + fmtQty(qty);
      frag.appendChild(opt);
    });

    selUbic.innerHTML = "";
    selUbic.appendChild(frag);

    if (prev) {
      const exists = Array.from(selUbic.options).some((o) => String(o.value) === String(prev));
      if (exists) selUbic.value = prev;
      else selUbic.value = "";
    }

    selUbic.disabled = !withStock.length;
  }

  function updateStockPanel(tipoKey, productoId, stockPack) {
    const b1 = $("stock_actual_badge");
    const b2 = $("stock_quedara_badge");
    const msg = $("stock_msg");
    const errStock = $("err_stock");

    if (!b1 || !b2) return;

    const selUbic = $("id_ubicacion");
    const selCant = $("id_cantidad");

    const ubicId = selUbic ? String(selUbic.value || "") : "";
    const qtyMov = selCant ? toNum(selCant.value) : 0;

    b1.textContent = "Stock: —";
    b2.textContent = "Quedará: —";
    if (msg) msg.textContent = "";
    if (errStock) errStock.classList.add("hidden");

    if (!productoId) {
      if (msg) msg.textContent = "Elegí un producto para ver el stock por ubicación.";
      return;
    }

    if (!ubicId) {
      if (msg) msg.textContent = "Elegí una ubicación.";
      return;
    }

    const current = stockPack && stockPack.map ? Number(stockPack.map.get(ubicId) || 0) : 0;
    b1.textContent = "Stock: " + fmtQty(current);

    const subtract = tipoKey === "EGRESO" || tipoKey === "TRANSFERENCIA";
    const after = subtract ? current - qtyMov : current + qtyMov;
    b2.textContent = "Quedará: " + fmtQty(after);

    if (subtract && qtyMov > 0 && after < 0) {
      if (msg) msg.textContent = "No alcanza el stock en esa ubicación.";
      if (errStock) errStock.classList.remove("hidden");
    }
  }

  function validateVisual(tipoKey, stockPack) {
    const producto = $("id_producto");
    const ubic = $("id_ubicacion");
    const cant = $("id_cantidad");
    const destino = $("id_ubicacion_destino");

    const errProducto = $("err_producto");
    const errTipo = $("err_tipo");
    const errOrigen = $("err_origen");
    const errDestino = $("err_destino");
    const errCantidad = $("err_cantidad");
    const errStock = $("err_stock");

    let ok = true;

    function show(el, should) {
      if (!el) return;
      if (should) el.classList.remove("hidden");
      else el.classList.add("hidden");
    }

    show(errProducto, !(producto && producto.value));
    if (!(producto && producto.value)) ok = false;

    show(errTipo, !tipoKey);
    if (!tipoKey) ok = false;

    show(errOrigen, !(ubic && ubic.value) || (ubic && ubic.disabled));
    if (!(ubic && ubic.value) || (ubic && ubic.disabled)) ok = false;

    const isTransfer = tipoKey === "TRANSFERENCIA";
    show(errDestino, isTransfer && !(destino && destino.value));
    if (isTransfer && !(destino && destino.value)) ok = false;

    if (isTransfer && ubic && destino && ubic.value && destino.value && ubic.value === destino.value) {
      show(errDestino, true);
      ok = false;
    }

    const num = cant ? toNum(cant.value) : 0;
    const qtyOk = num > 0;
    show(errCantidad, !qtyOk);
    if (!qtyOk) ok = false;

    const subtract = tipoKey === "EGRESO" || tipoKey === "TRANSFERENCIA";
    if (subtract && stockPack && stockPack.map && ubic && ubic.value) {
      const current = Number(stockPack.map.get(String(ubic.value)) || 0);
      const enough = !(num > current);
      show(errStock, !enough);
      if (!enough) ok = false;
    } else {
      show(errStock, false);
    }

    return ok;
  }

  document.addEventListener("DOMContentLoaded", function () {
    const tipoSel = getTipoSelect();
    const pills = document.querySelectorAll("#tipo_pills [data-tipo]");
    const selProd = $("id_producto");
    const selUbic = $("id_ubicacion");
    const selCant = $("id_cantidad");
    const selDestino = $("id_ubicacion_destino");
    const form = document.querySelector("form");

    const map = buildTipoMap();

    const ubicAllCache = selUbic ? buildSelectCache(selUbic) : [];

    // ✅ Se arma una sola vez (antes se reconstruía cada refresh)
    const ubicLabelMap = new Map();
    ubicAllCache.forEach((it) => {
      if (it.value) ubicLabelMap.set(String(it.value), it.text);
    });

    let tipoKey = "";
    let productoId = selProd ? safeStr(selProd.value) : "";
    let stockPack = { map: new Map(), list: [] };

    function refreshStockAndOrigen() {
      productoId = selProd ? safeStr(selProd.value) : "";

      // Cancelar request anterior (si el browser soporta AbortController)
      if (typeof AbortController !== "undefined") {
        if (stockAbort) stockAbort.abort();
        stockAbort = new AbortController();
      } else {
        stockAbort = null;
      }

      const mySeq = ++refreshSeq;

      const signal = stockAbort ? stockAbort.signal : undefined;

      return fetchStock(productoId, signal).then((pack) => {
        // Evita que una respuesta vieja pise el estado actual
        if (mySeq !== refreshSeq) return pack;

        stockPack = pack;
        applyOrigenFilter(tipoKey, productoId, stockPack, ubicAllCache, ubicLabelMap);
        updateStockPanel(tipoKey, productoId, stockPack);
        return pack;
      });
    }

    if (tipoSel && !safeStr(tipoSel.value)) {
      setTipoByKey("INGRESO", map);
    }

    tipoKey = keyFromSelect(map) || "INGRESO";
    setPillsActive(tipoKey);
    setDestinoVisibility(tipoKey);
    toggleOptionalByTipo(tipoKey);

    refreshStockAndOrigen();

    pills.forEach((btn) => {
      btn.addEventListener("click", function () {
        const k = upper(btn.getAttribute("data-tipo"));
        if (!k) return;

        setTipoByKey(k, map);
        tipoKey = k;
        setPillsActive(tipoKey);
        setDestinoVisibility(tipoKey);
        toggleOptionalByTipo(tipoKey);

        refreshStockAndOrigen();
        focusCantidad();
      });
    });

    if (tipoSel) {
      tipoSel.addEventListener("change", function () {
        tipoSel.disabled = false;
        tipoKey = keyFromSelect(map) || "INGRESO";
        setPillsActive(tipoKey);
        setDestinoVisibility(tipoKey);
        toggleOptionalByTipo(tipoKey);
        refreshStockAndOrigen();
      });
    }

    if (selProd) {
      selProd.addEventListener("change", function () {
        const opt = selProd.options[selProd.selectedIndex];
        saveLastProduct(selProd.value, opt ? opt.textContent.trim() : selProd.value);
        renderLastProducts();
        refreshStockAndOrigen();
        focusCantidad();
      });
    }

    if (selUbic) {
      selUbic.addEventListener("change", function () {
        updateStockPanel(tipoKey, productoId, stockPack);
        if (tipoKey === "TRANSFERENCIA" && selDestino && selDestino.value && selDestino.value === selUbic.value) {
          selDestino.value = "";
        }
      });
    }

    if (selCant) {
      selCant.addEventListener("input", function () {
        updateStockPanel(tipoKey, productoId, stockPack);
      });
    }

    if (selDestino) {
      selDestino.addEventListener("change", function () {
        updateStockPanel(tipoKey, productoId, stockPack);
      });
    }

    if (form) {
      form.addEventListener("submit", function (e) {
        if (tipoSel) tipoSel.disabled = false;
        const k = keyFromSelect(map) || "INGRESO";
        if (tipoSel && !safeStr(tipoSel.value)) {
          setTipoByKey(k, map);
        }
        if (!validateVisual(k, stockPack)) {
          e.preventDefault();
          updateStockPanel(k, productoId, stockPack);
        }
      });
    }

    renderLastProducts();
    initProductSearch();
  });
})();