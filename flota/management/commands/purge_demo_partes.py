from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Q

from flota.partes_models import ParteDiario


class Command(BaseCommand):
    help = "Elimina partes de prueba (por ejemplo: 'Parte generado para pruebas')."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Ejecuta el borrado. Sin --yes solo muestra qué eliminaría.",
        )
        parser.add_argument(
            "--contains",
            default="generado para pruebas",
            help="Texto a buscar en descripcion (default: 'generado para pruebas').",
        )

    def handle(self, *args, **opts):
        contains = (opts.get("contains") or "").strip()
        if not contains:
            self.stderr.write(self.style.ERROR("El parámetro --contains no puede ser vacío."))
            return

        qs = ParteDiario.objects.filter(Q(descripcion__icontains=contains) | Q(observaciones__icontains=contains)).order_by("-fecha_evento", "-id")
        total = qs.count()

        self.stdout.write(f"Coincidencias a eliminar: {total}")
        for p in qs[:50]:
            self.stdout.write(f"- PD-{p.id} | {p.fecha_evento:%Y-%m-%d %H:%M} | {p.tipo} | Int {p.colectivo.interno} | {p.resumen}")

        if total > 50:
            self.stdout.write(f"(Mostrando 50 de {total})")

        if not opts.get("yes"):
            self.stdout.write("Dry-run. Para borrar, ejecutar con --yes.")
            return

        deleted = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"OK: eliminados {deleted[0]} registros (incluye adjuntos en cascada si aplica)."))
