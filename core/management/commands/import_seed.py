from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    help = "Importa un seed (fixture JSON) generado por export_seed. No requiere internet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            required=True,
            help="Ruta del fixture JSON (ej: seed/seed_export.json)",
        )

    def handle(self, *args, **opts):
        p = Path(opts["path"])
        if not p.exists():
            raise CommandError(f"No existe el archivo: {p}")

        self.stdout.write(f"Importando fixture: {p.as_posix()}")
        call_command("loaddata", p.as_posix())
        self.stdout.write(self.style.SUCCESS("OK: seed importado."))
