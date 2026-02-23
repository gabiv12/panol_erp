from __future__ import annotations

import re
from django.core.management.base import BaseCommand
from django.db import transaction

from flota.models import Colectivo
from inventario.models import MovimientoStock


# Captura interno cuando viene con palabra clave cerca
RX_KEYED_INT = re.compile(
    r"\b(?:INT(?:ERNO)?|UNIDAD|COLECTIVO|BUS|C)\s*[:#\-]?\s*(\d{1,4})\b",
    re.IGNORECASE
)

# También soporta "INT-14" o "INT 14"
RX_INT_SIMPLE = re.compile(r"\bINT\s*[- ]\s*(\d{1,4})\b", re.IGNORECASE)


def _normalize(s: str) -> str:
    # Normaliza para comparar dominios aunque haya espacios o guiones
    s = (s or "").upper()
    return re.sub(r"[\s\-\._]", "", s)


class Command(BaseCommand):
    help = (
        "Completa MovimientoStock.colectivo en movimientos con colectivo=NULL "
        "a partir de referencia/observaciones/lote.\n"
        "Detecta internos por patrones (INT-14, interno 14, unidad:14, #14) y dominio."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Simula sin guardar cambios.")
        parser.add_argument("--limit", type=int, default=0, help="Limita cantidad a procesar (0 = sin límite).")
        parser.add_argument("--show-unmatched", type=int, default=10, help="Muestra N ejemplos que no matchearon (0 = no mostrar).")

    def handle(self, *args, **opts):
        dry = bool(opts["dry_run"])
        limit = int(opts["limit"] or 0)
        show_unmatched = int(opts["show_unmatched"] or 0)

        colectivos = list(Colectivo.objects.filter(is_active=True).only("id", "interno", "dominio"))
        by_interno = {c.interno: c for c in colectivos}
        by_dom_norm = {}
        for c in colectivos:
            dom = (c.dominio or "").strip().upper()
            if dom:
                by_dom_norm[_normalize(dom)] = c

        qs = MovimientoStock.objects.filter(colectivo__isnull=True).only(
            "id", "referencia", "observaciones", "lote"
        ).order_by("-id")

        if limit > 0:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f"Movimientos a evaluar (colectivo=NULL): {total}")

        found = 0
        updated = 0
        blank = 0
        not_found = 0
        examples_unmatched = []

        updates = []

        for m in qs.iterator(chunk_size=500):
            text = f"{m.referencia or ''} {m.observaciones or ''} {m.lote or ''}".strip()
            if not text:
                blank += 1
                continue

            target = None

            mm = RX_KEYED_INT.search(text) or RX_INT_SIMPLE.search(text)
            if mm:
                interno = int(mm.group(1))
                target = by_interno.get(interno)

            if target is None and by_dom_norm:
                ntext = _normalize(text)
                for dom_norm, c in by_dom_norm.items():
                    if dom_norm and dom_norm in ntext:
                        target = c
                        break

            if target is None:
                not_found += 1
                if show_unmatched > 0 and len(examples_unmatched) < show_unmatched:
                    examples_unmatched.append((m.id, text[:120]))
                continue

            found += 1
            updates.append((m.id, target.id))

        self.stdout.write(f"Detectados para completar: {found}")
        self.stdout.write(f"Sin texto (imposible auto): {blank}")
        self.stdout.write(f"Sin match: {not_found}")

        if show_unmatched > 0 and examples_unmatched:
            self.stdout.write("Ejemplos sin match (id -> texto):")
            for mid, snip in examples_unmatched:
                self.stdout.write(f" - {mid} -> {snip}")

        if dry:
            self.stdout.write("DRY-RUN: no se guardó nada.")
            return

        with transaction.atomic():
            for mov_id, col_id in updates:
                updated += MovimientoStock.objects.filter(id=mov_id, colectivo__isnull=True).update(colectivo_id=col_id)

        self.stdout.write(f"Actualizados: {updated}")