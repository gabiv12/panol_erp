from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


EXTS_DEFAULT = {".py", ".html", ".md", ".js", ".css", ".txt"}
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "media",
    "staticfiles",
}


def _looks_like_mojibake(s: str) -> bool:
    # patrones típicos de UTF-8 interpretado como Latin-1
    return any(x in s for x in ("Ã", "Â", "â€", "ðŸ", "\ufeff"))


def _try_fix(s: str) -> str | None:
    if not _looks_like_mojibake(s):
        return None

    # 1) quitar BOM si existe
    s2 = s.lstrip("\ufeff")

    # 2) intento estándar: latin1 -> utf-8
    try:
        fixed = s2.encode("latin1").decode("utf-8")
    except Exception:
        fixed = None

    if fixed and fixed != s2:
        # Heurística: reducir la cantidad de marcadores raros
        before = sum(s2.count(x) for x in ("Ã", "Â", "â€", "ðŸ"))
        after = sum(fixed.count(x) for x in ("Ã", "Â", "â€", "ðŸ"))
        if after < before:
            return fixed

    # 3) al menos devolver sin BOM si era lo único raro
    if s2 != s:
        return s2

    return None


class Command(BaseCommand):
    help = "Arregla textos con acentos rotos (ej: dÃ­a -> día) en archivos del repo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(settings.BASE_DIR),
            help="Ruta base a escanear (default: BASE_DIR).",
        )
        parser.add_argument(
            "--write",
            action="store_true",
            help="Escribe cambios (si no se indica, solo muestra el reporte).",
        )
        parser.add_argument(
            "--ext",
            action="append",
            help="Extensiones a incluir (repetible). Default: .py .html .md .js .css .txt",
        )

    def handle(self, *args, **opts):
        base = Path(opts["path"]).resolve()
        write = bool(opts["write"])
        exts = set(opts.get("ext") or [])
        if not exts:
            exts = set(EXTS_DEFAULT)
        exts = {e if e.startswith(".") else f".{e}" for e in exts}

        changed = 0
        scanned = 0
        errors: list[str] = []

        for root, dirs, files in os.walk(base):
            root_p = Path(root)

            # skip dirs
            dirs[:] = [
                d
                for d in dirs
                if d not in SKIP_DIRS and not d.startswith("backup_") and not d.startswith("_patch_apply_")
            ]

            for fn in files:
                p = (root_p / fn)
                if p.suffix.lower() not in exts:
                    continue

                scanned += 1
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    # si no es utf-8, no tocamos (evita binarios o archivos raros)
                    continue

                fixed = _try_fix(text)
                if fixed is None:
                    continue

                changed += 1
                self.stdout.write(f"FIX: {p.relative_to(base)}")

                if write:
                    p.write_text(fixed, encoding="utf-8", newline="\n")

        self.stdout.write("")
        self.stdout.write(f"Escaneados: {scanned} | Para corregir: {changed}")
        if not write and changed:
            self.stdout.write("Ejecutá con --write para aplicar cambios.")

