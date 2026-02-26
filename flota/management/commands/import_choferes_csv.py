from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from flota.choferes_models import Chofer


class Command(BaseCommand):
    help = "Importa choferes desde CSV (apellido,nombre,legajo,telefono,observaciones,is_active)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Ruta al CSV (ej: seed/choferes.csv)")

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        if not csv_path.exists():
            raise CommandError(f"No existe: {csv_path}")

        created = 0
        updated = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ap = (row.get("apellido") or "").strip()
                no = (row.get("nombre") or "").strip()
                if not ap or not no:
                    continue

                legajo = (row.get("legajo") or "").strip() or None
                telefono = (row.get("telefono") or "").strip()
                obs = (row.get("observaciones") or "").strip()
                is_active_raw = (row.get("is_active") or "").strip().lower()
                is_active = True if is_active_raw in ("", "1", "true", "si", "sí", "s") else False

                if legajo:
                    _, was_created = Chofer.objects.update_or_create(
                        legajo=legajo,
                        defaults={"apellido": ap, "nombre": no, "telefono": telefono, "observaciones": obs, "is_active": is_active},
                    )
                else:
                    _, was_created = Chofer.objects.get_or_create(
                        apellido=ap,
                        nombre=no,
                        defaults={"telefono": telefono, "observaciones": obs, "is_active": is_active},
                    )

                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(self.style.SUCCESS(f"OK. Creados: {created} | Actualizados: {updated}"))
