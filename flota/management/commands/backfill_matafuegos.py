from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from flota.models import Colectivo


class Command(BaseCommand):
    help = "Sincroniza datos legacy de matafuegos hacia campos nuevos y mantiene compatibilidad."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No guarda cambios, solo muestra conteo.")

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run"))
        qs = Colectivo.objects.all()

        to_update = []
        changed = 0

        for c in qs:
            v1 = c.matafuego_1_vto
            v2 = c.matafuego_2_vto

            legacy1 = getattr(c, "matafuego_vto", None)
            legacy2 = getattr(c, "matafuego_vencimiento_2", None)

            did = False

            if not v1 and legacy1:
                c.matafuego_1_vto = legacy1
                v1 = legacy1
                did = True

            if not v2 and legacy2:
                c.matafuego_2_vto = legacy2
                v2 = legacy2
                did = True

            fechas = [d for d in (v1, v2) if d]
            prox = min(fechas) if fechas else None

            if getattr(c, "matafuego_vto", None) != prox:
                c.matafuego_vto = prox
                did = True

            if hasattr(c, "matafuego_vencimiento_2") and getattr(c, "matafuego_vencimiento_2", None) != v2:
                c.matafuego_vencimiento_2 = v2
                did = True

            if did:
                changed += 1
                to_update.append(c)

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"DRY RUN: {changed} unidades serían actualizadas."))
            return

        with transaction.atomic():
            for c in to_update:
                c.save(update_fields=[
                    "matafuego_1_vto",
                    "matafuego_2_vto",
                    "matafuego_vto",
                    "matafuego_vencimiento_2",
                ])

        self.stdout.write(self.style.SUCCESS(f"OK: {changed} unidades actualizadas."))
