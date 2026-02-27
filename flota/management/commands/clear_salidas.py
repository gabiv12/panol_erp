from __future__ import annotations

from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date
from django.utils import timezone

from flota.models import SalidaProgramada


class Command(BaseCommand):
    help = "Borra salidas programadas en un rango de fechas (inclusive). Útil para limpiar datos de prueba."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD (inclusive)")
        parser.add_argument("--to", dest="to_date", required=True, help="YYYY-MM-DD (inclusive)")
        parser.add_argument("--yes", action="store_true", help="Ejecuta el borrado. Sin esto, solo muestra cuántas borraría.")

    def handle(self, *args, **opts):
        d1 = parse_date(opts["from_date"])
        d2 = parse_date(opts["to_date"])
        if not d1 or not d2:
            raise CommandError("Fechas inválidas. Usá formato YYYY-MM-DD.")
        if d2 < d1:
            raise CommandError("--to debe ser >= --from.")

        tz = timezone.get_current_timezone()
        start = timezone.make_aware(timezone.datetime.combine(d1, timezone.datetime.min.time()), tz)
        end_excl = timezone.make_aware(timezone.datetime.combine(d2 + timedelta(days=1), timezone.datetime.min.time()), tz)

        qs = SalidaProgramada.objects.filter(salida_programada__gte=start, salida_programada__lt=end_excl)
        count = qs.count()

        self.stdout.write(f"Rango: {d1} .. {d2}")
        self.stdout.write(f"Coinciden: {count} salidas")

        if not opts["yes"]:
            self.stdout.write("DRY-RUN: no se borró nada. Agregá --yes para ejecutar.")
            return

        qs.delete()
        self.stdout.write(self.style.SUCCESS("OK: salidas borradas."))
