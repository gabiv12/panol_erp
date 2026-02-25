from __future__ import annotations

"""Hotfix in-place:
- static/js/app.js: drawer IDs + hidden/translate support
- inventario/views.py: MovimientoStockCreateView.form_valid rollback real
"""

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve()

def patch_app_js():
    p = ROOT / "static" / "js" / "app.js"
    if not p.exists():
        print(f"[WARN] No existe: {p}")
        return
    s = p.read_text(encoding="utf-8")

    pat = re.compile(r"(?s)// =====================\n  // Drawer \(mobile sidebar\)\n  // =====================\n.*?// =====================\n  // Clock")
    if not pat.search(s):
        print("[WARN] No encontré bloque Drawer en app.js (no se tocó).")
        return

    repl = """  // =====================
  // Drawer (mobile sidebar)
  // =====================
  // Soporta dos layouts:
  // - IDs nuevos:   #drawer y #drawerOverlay (templates actuales)
  // - IDs legacy:   #tiDrawer y #tiOverlay (compatibilidad)
  const drawer = () => document.getElementById("drawer") || document.getElementById("tiDrawer");
  const overlay = () => document.getElementById("drawerOverlay") || document.getElementById("tiOverlay");

  function openDrawer() {
    const d = drawer();
    const o = overlay();
    if (!d || !o) return;

    // Algunos templates usan 'hidden', otros usan translate.
    d.classList.remove("hidden");
    d.classList.remove("-translate-x-full");

    o.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  function closeDrawer() {
    const d = drawer();
    const o = overlay();
    if (!d || !o) return;

    // Si el drawer usa translate, respetamos animación y luego ocultamos.
    const usesTranslate = d.classList.contains("transition") || d.classList.contains("duration-300") || d.classList.contains("-translate-x-full");
    if (usesTranslate) {
      d.classList.add("-translate-x-full");
      window.setTimeout(() => d.classList.add("hidden"), 200);
    } else {
      d.classList.add("hidden");
    }

    o.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  function initDrawer() {
    document.addEventListener("click", (ev) => {
      if (ev.target.closest("[data-drawer-open]")) {
        openDrawer();
        return;
      }
      if (ev.target.closest("[data-drawer-close]")) {
        closeDrawer();
        return;
      }
      if (ev.target === overlay()) {
        closeDrawer();
      }
    });

    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") closeDrawer();
    });
  }

  // =====================
  // Clock"""
    s2 = pat.sub(repl, s)
    if s2 != s:
        p.write_text(s2, encoding="utf-8")
        print("[OK] app.js actualizado (drawer mobile).")
    else:
        print("[OK] app.js ya estaba actualizado.")

def patch_inventario_views():
    p = ROOT / "inventario" / "views.py"
    if not p.exists():
        print(f"[WARN] No existe: {p}")
        return
    s = p.read_text(encoding="utf-8")

    m = re.search(r"(?s)(class\s+MovimientoStockCreateView\(.*?\):)(.*?)(?=^class\s+MovimientoStockUpdateView\b)", s, flags=re.M)
    if not m:
        print("[WARN] No encontré class MovimientoStockCreateView (no se tocó).")
        return

    head, body = m.group(1), m.group(2)
    tail = s[m.end():]

    fv = re.search(r"(?s)^\s+def\s+form_valid\s*\(self,\s*form\):.*\Z", body, flags=re.M)
    if not fv:
        print("[WARN] No encontré form_valid dentro de MovimientoStockCreateView (no se tocó).")
        return

    new_fv = """    def form_valid(self, form):
        """
        Crea movimiento + aplica stock.

        Importante: si venís del informe de una unidad con force=1, forzamos colectivo_id aunque el usuario no lo toque.
        """

        # Forzar unidad cuando viene del informe (evita que quede NULL por error humano)
        force = (self.request.GET.get("force") or "").strip() in ("1", "true", "True", "on")
        col_raw = self.request.GET.get("colectivo") or self.request.GET.get("colectivo_id")
        col_id = None
        try:
            if col_raw:
                col_id = int(col_raw)
        except Exception:
            col_id = None

        if force and col_id and not getattr(form.instance, "colectivo_id", None):
            form.instance.colectivo_id = col_id

        try:
            with transaction.atomic():
                response = super().form_valid(form)
                # Aplica stock (si falla, se hace rollback completo)
                stock_service.aplicar_movimiento_creado(self.object)

            messages.success(self.request, "Movimiento registrado correctamente.")
            return response

        except ValueError as e:
            msg = str(e)

            # Microcopy más útil cuando el problema es stock
            if "Stock insuficiente" in msg:
                msg = msg + " Primero registrá una entrada para cargar stock (o elegí otra ubicación)."

            messages.error(self.request, msg)
            form.add_error(None, msg)
            return self.form_invalid(form)
"""

    body2 = body[:fv.start()] + "\n" + new_fv + "\n"
    s2 = s[:m.start()] + head + body2 + tail

    if s2 != s:
        p.write_text(s2, encoding="utf-8")
        print("[OK] inventario/views.py actualizado (rollback real + microcopy).")
    else:
        print("[OK] inventario/views.py ya estaba actualizado.")

def main():
    patch_app_js()
    patch_inventario_views()

if __name__ == "__main__":
    main()
