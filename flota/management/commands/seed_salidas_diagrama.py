from __future__ import annotations

"""
Comando de carga inicial (seed) para Salidas programadas.

Uso recomendado (para ver el sistema "con datos"):
- Crear un CSV a partir del diagrama real (Excel/Google Sheets).
- Importar el CSV para una fecha específica.

Formato CSV (encabezados):
- interno (obligatorio) : número interno de la unidad
- salida_hora (obligatorio) : HH:MM
- seccion : grupo del diagrama (como papel)
- salida_label : etiqueta corta (como papel)
- regreso : texto de regreso (12:00 DIR / **)
- chofer
- recorrido
- tipo : NORMAL o ESPECIAL (si se omite, NORMAL)
- estado : PROGRAMADA (si se omite, PROGRAMADA)
- nota
- llegada_hora : HH:MM (opcional)

El comando NO toca inventario ni partes diarios; solo Horarios.
"""

import csv
from datetime import datetime, time as dtime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from flota.models import Colectivo, SalidaProgramada


class Command(BaseCommand):
    help = "Importa salidas programadas desde un CSV (seed) para una fecha."

    def add_arguments(self, parser):
        parser.add_argument("--fecha", type=str, default="", help="YYYY-MM-DD. Si se omite, usa mañana.")
        parser.add_argument("--csv", type=str, default="seed/diagrama_template.csv", help="Ruta al CSV.")
        parser.add_argument("--dry-run", action="store_true", help="No guarda, solo muestra resumen.")
        parser.add_argument("--create-missing-colectivos", action="store_true", help="Crea colectivos si falta el interno.")

    def handle(self, *args, **opts):
        fecha = (opts["fecha"] or "").strip()
        csv_path = (opts["csv"] or "").strip()
        dry = bool(opts["dry_run"])
        create_missing = bool(opts["create_missing_colectivos"])

        if fecha:
            try:
                day = datetime.fromisoformat(fecha).date()
            except Exception:
                raise SystemExit("Fecha inválida. Usá YYYY-MM-DD.")
        else:
            day = timezone.localdate() + timedelta(days=1)

        def parse_hhmm(s: str) -> dtime:
            s = (s or "").strip()
            if not s:
                raise ValueError("hora vacía")
            parts = s.split(":")
            if len(parts) < 2:
                raise ValueError("hora inválida")
            h = int(parts[0])
            m = int(parts[1])
            return dtime(h, m)

        created = 0
        skipped = 0

        try:
            fh = open(csv_path, "r", encoding="utf-8-sig", newline="")
        except FileNotFoundError:
            raise SystemExit(f"No existe el CSV: {csv_path}")

        with fh:
            reader = csv.DictReader(fh)
            required = {"interno", "salida_hora"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise SystemExit(f"Faltan columnas requeridas en CSV: {', '.join(sorted(missing))}")

            for row in reader:
                interno_raw = (row.get("interno") or "").strip()
                if not interno_raw.isdigit():
                    skipped += 1
                    continue
                interno = int(interno_raw)

                try:
                    salida_t = parse_hhmm(row.get("salida_hora") or "")
                except Exception:
                    skipped += 1
                    continue

                salida_dt = timezone.make_aware(datetime.combine(day, salida_t))

                c = Colectivo.objects.filter(interno=interno).first()
                if not c:
                    if not create_missing:
                        skipped += 1
                        continue
                    c = Colectivo.objects.create(
                        interno=interno,
                        dominio=(row.get("dominio") or f"INT{interno}").upper(),
                        marca="",
                        modelo="",
                        is_active=True,
                    )

                # Evitar duplicados exactos
                if SalidaProgramada.objects.filter(colectivo=c, salida_programada=salida_dt).exists():
                    skipped += 1
                    continue

                llegada_dt = None
                llegada_h = (row.get("llegada_hora") or "").strip()
                if llegada_h:
                    try:
                        llegada_t = parse_hhmm(llegada_h)
                        llegada_dt = timezone.make_aware(datetime.combine(day, llegada_t))
                    except Exception:
                        llegada_dt = None

                obj = SalidaProgramada(
                    colectivo=c,
                    salida_programada=salida_dt,
                    llegada_programada=llegada_dt,
                    tipo=(row.get("tipo") or SalidaProgramada.Tipo.NORMAL),
                    estado=(row.get("estado") or SalidaProgramada.Estado.PROGRAMADA),
                    seccion=(row.get("seccion") or "").strip(),
                    salida_label=(row.get("salida_label") or "").strip(),
                    regreso=(row.get("regreso") or "").strip(),
                    chofer=(row.get("chofer") or "").strip(),
                    recorrido=(row.get("recorrido") or "").strip(),
                    nota=(row.get("nota") or "").strip(),
                )

                if dry:
                    created += 1
                else:
                    obj.save()
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"Fecha: {day}"))
        self.stdout.write(self.style.SUCCESS(f"Creadas: {created}"))
        self.stdout.write(self.style.WARNING(f"Omitidas: {skipped}"))
        if dry:
            self.stdout.write(self.style.WARNING("DRY-RUN: no se guardó nada."))
