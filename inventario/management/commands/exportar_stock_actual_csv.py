from __future__ import annotations

import csv
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Q

from inventario.models import StockActual


class Command(BaseCommand):
    help = "Exporta el StockActual a un CSV (útil para ordenar y planificar el depósito)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            required=True,
            help="Ruta destino del CSV (ej: C:\\Users\\...\\Downloads\\stock_actual.csv).",
        )
        parser.add_argument(
            "--include-zero",
            action="store_true",
            help="Incluir filas con cantidad = 0 (por defecto se omiten).",
        )
        parser.add_argument(
            "--delimiter",
            default=";",
            help="Separador CSV. Recomendado ';' para Excel en AR. Default=';'.",
        )

    def handle(self, *args, **opts):
        out = opts["out"]
        include_zero = bool(opts["include_zero"])
        delim = opts["delimiter"] or ";"

        qs = (
            StockActual.objects.select_related("producto", "producto__unidad_medida", "ubicacion")
            .order_by("producto__codigo", "ubicacion__codigo")
        )
        if not include_zero:
            qs = qs.exclude(cantidad=Decimal("0"))

        total = qs.count()

        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=delim)
            w.writerow(
                [
                    "producto_codigo",
                    "producto_nombre",
                    "unidad",
                    "permite_decimales",
                    "ubicacion_codigo",
                    "ubicacion_path",
                    "ubicacion_nombre",
                    "cantidad",
                ]
            )
            for s in qs.iterator():
                um = s.producto.unidad_medida
                ubic = s.ubicacion
                ubic_path = ubic.path_codigos() if hasattr(ubic, "path_codigos") else ubic.codigo
                w.writerow(
                    [
                        s.producto.codigo,
                        s.producto.nombre,
                        getattr(um, "abreviatura", ""),
                        "1" if getattr(um, "permite_decimales", False) else "0",
                        ubic.codigo,
                        ubic_path,
                        ubic.nombre,
                        str(s.cantidad),
                    ]
                )

        self.stdout.write(self.style.SUCCESS(f"OK: exportado {total} filas a {out}"))
