from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


DEFAULT_APPS = ["flota", "inventario", "adjuntos"]


class Command(BaseCommand):
    help = "Exporta un seed (fixture JSON) de datos operativos. No requiere internet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            default="seed/seed_export.json",
            help="Ruta del archivo .json a generar (por defecto: seed/seed_export.json)",
        )
        parser.add_argument(
            "--apps",
            nargs="*",
            default=DEFAULT_APPS,
            help=f"Apps a exportar (por defecto: {', '.join(DEFAULT_APPS)})",
        )
        parser.add_argument(
            "--include-auth",
            action="store_true",
            help="Incluye auth.User + auth.Group (puede contener passwords hash). Usar solo si es necesario.",
        )

    def handle(self, *args, **opts):
        out_path = Path(opts["out"]).as_posix()
        apps: List[str] = list(opts["apps"] or [])
        include_auth = bool(opts["include_auth"])

        if not apps:
            raise CommandError("Tenés que indicar al menos una app en --apps.")

        out_dir = Path(out_path).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        targets = list(apps)
        if include_auth:
            targets += ["auth.user", "auth.group"]

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stdout.write(f"Exportando seed ({stamp}) -> {out_path}")
        self.stdout.write("Incluye: " + ", ".join(targets))

        # exclude contenttypes/permissions porque hacen el fixture más frágil
        call_command(
            "dumpdata",
            *targets,
            indent=2,
            natural_foreign=True,
            natural_primary=True,
            exclude=["contenttypes", "admin", "sessions"],
            output=out_path,
        )

        self.stdout.write(self.style.SUCCESS("OK: seed exportado."))
        self.stdout.write(f"Archivo: {out_path}")
