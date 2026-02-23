from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.db.models import Sum

from inventario.models import StockActual


class Command(BaseCommand):
    help = "Normaliza StockActual: elimina duplicados por (producto, ubicacion) y suma cantidades."

    @transaction.atomic
    def handle(self, *args, **options):
        mgr = StockActual._base_manager  # por si en el futuro hay manager filtrado
        dups = (
            mgr.values("producto_id", "ubicacion_id")
            .annotate(n=models.Count("id"))
            .filter(n__gt=1)
        )

        if not dups.exists():
            self.stdout.write(self.style.SUCCESS("OK: No hay duplicados en StockActual."))
            return

        fixed = 0
        for row in dups:
            pid = row["producto_id"]
            uid = row["ubicacion_id"]

            qs = mgr.filter(producto_id=pid, ubicacion_id=uid).order_by("id")
            keep = qs.first()

            if hasattr(keep, "cantidad"):
                total = qs.aggregate(total=Sum("cantidad"))["total"] or 0
                keep.cantidad = total
                keep.save(update_fields=["cantidad"])

            qs.exclude(id=keep.id).delete()
            fixed += 1

        self.stdout.write(self.style.SUCCESS(f"OK: normalizados {fixed} pares duplicados (producto, ubicacion)."))
