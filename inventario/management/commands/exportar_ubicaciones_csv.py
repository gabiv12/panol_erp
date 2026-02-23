from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from inventario.models import Ubicacion


class Command(BaseCommand):
    help = "Exporta ubicaciones a CSV (para etiquetas / auditoría)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            default="ubicaciones_export.csv",
            help="Archivo de salida (relativo al proyecto o ruta absoluta). Default: ubicaciones_export.csv",
        )

    def handle(self, *args, **opts):
        out = Path(opts["out"]).expanduser().resolve()
        qs = Ubicacion.objects.all().order_by("codigo")

        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "codigo",
                    "nombre",
                    "tipo",
                    "padre",
                    "pasillo",
                    "modulo",
                    "nivel",
                    "posicion",
                    "permite_transferencias",
                    "is_active",
                ]
            )
            for u in qs:
                w.writerow(
                    [
                        u.codigo,
                        u.nombre,
                        u.tipo,
                        u.padre.codigo if u.padre else "",
                        u.pasillo or "",
                        u.modulo if u.modulo is not None else "",
                        u.nivel if u.nivel is not None else "",
                        u.posicion if u.posicion is not None else "",
                        "1" if u.permite_transferencias else "0",
                        "1" if u.is_active else "0",
                    ]
                )

        self.stdout.write(self.style.SUCCESS(f"OK: exportado {qs.count()} ubicaciones a {out}"))
