from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from flota.models import Colectivo, SalidaProgramada


@dataclass(frozen=True)
class TemplateRow:
    interno: int
    salida_hora: time
    seccion: str
    salida_label: str
    regreso: str
    chofer: str
    recorrido: str
    tipo: str
    estado: str
    nota: str
    llegada_hora: time | None


def _parse_hhmm(value: str) -> time:
    v = (value or "").strip()
    if not v:
        raise ValueError("hora vacía")
    # Admite HH:MM
    return datetime.strptime(v, "%H:%M").time()


def _to_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except Exception as e:
        raise CommandError(f"Fecha inválida '{value}'. Usá YYYY-MM-DD.") from e


def _map_tipo(raw: str) -> str:
    v = (raw or "").strip().upper()
    if v == SalidaProgramada.Tipo.ESPECIAL:
        return SalidaProgramada.Tipo.ESPECIAL
    return SalidaProgramada.Tipo.NORMAL


def _map_estado(raw: str) -> str:
    v = (raw or "").strip().upper()
    valid = {c for c, _ in SalidaProgramada.Estado.choices}
    return v if v in valid else SalidaProgramada.Estado.PROGRAMADA


def _make_aware(dt: datetime) -> datetime:
    # Respeta TIME_ZONE + USE_TZ.
    if timezone.is_aware(dt):
        return dt
    tz = timezone.get_current_timezone()
    return timezone.make_aware(dt, tz)


def _day_bounds(d: date) -> tuple[datetime, datetime]:
    start = _make_aware(datetime.combine(d, time.min))
    end = _make_aware(datetime.combine(d, time.max))
    # time.max incluye microsegundos; preferimos [start, next_day_start)
    end = _make_aware(datetime.combine(d + timedelta(days=1), time.min))
    return start, end


def _load_template_rows(path: Path) -> list[TemplateRow]:
    if not path.exists():
        raise CommandError(f"No existe el template CSV: {path}")

    rows: list[TemplateRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "interno",
            "salida_hora",
            "seccion",
            "salida_label",
            "regreso",
            "chofer",
            "recorrido",
            "tipo",
            "estado",
            "nota",
            "llegada_hora",
        }
        missing_cols = required - set(reader.fieldnames or [])
        if missing_cols:
            raise CommandError(f"El CSV no tiene columnas requeridas: {', '.join(sorted(missing_cols))}")

        for i, r in enumerate(reader, start=2):
            try:
                interno = int((r.get("interno") or "").strip())
                salida_hora = _parse_hhmm(r.get("salida_hora") or "")
                seccion = (r.get("seccion") or "").strip()
                salida_label = (r.get("salida_label") or "").strip()
                regreso = (r.get("regreso") or "").strip()
                chofer = (r.get("chofer") or "").strip()
                recorrido = (r.get("recorrido") or "").strip()
                tipo = _map_tipo(r.get("tipo") or "")
                estado = _map_estado(r.get("estado") or "")
                nota = (r.get("nota") or "").strip()

                llegada_raw = (r.get("llegada_hora") or "").strip()
                llegada_hora = _parse_hhmm(llegada_raw) if llegada_raw else None

                if not seccion or not salida_label:
                    raise ValueError("seccion/salida_label vacíos")

                rows.append(
                    TemplateRow(
                        interno=interno,
                        salida_hora=salida_hora,
                        seccion=seccion,
                        salida_label=salida_label,
                        regreso=regreso,
                        chofer=chofer,
                        recorrido=recorrido,
                        tipo=tipo,
                        estado=estado,
                        nota=nota,
                        llegada_hora=llegada_hora,
                    )
                )
            except Exception as e:
                raise CommandError(f"Error en CSV línea {i}: {e}") from e

    if not rows:
        raise CommandError("El CSV está vacío.")

    return rows


class Command(BaseCommand):
    help = "Crea horarios fijos (SalidaProgramada) para un rango de días desde seed/diagrama_template.csv."

    def add_arguments(self, parser):
        parser.add_argument("--fecha", required=True, help="Fecha inicial (YYYY-MM-DD)")
        parser.add_argument("--days", type=int, default=60, help="Cantidad de días a generar")
        parser.add_argument(
            "--template",
            default="seed/diagrama_template.csv",
            help="Ruta al CSV de template (relativa a BASE_DIR o absoluta)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Borra salidas del rango (solo NORMAL) antes de recrear. No toca ESPECIAL.",
        )
        parser.add_argument("--dry-run", action="store_true", help="No escribe en DB; solo valida y muestra resumen")

    @transaction.atomic
    def handle(self, *args, **opts):
        start_day = _to_date(opts["fecha"])
        days = int(opts["days"])
        if days <= 0 or days > 366:
            raise CommandError("--days debe estar entre 1 y 366")

        tpl_arg = str(opts["template"])
        tpl_path = Path(tpl_arg)
        if not tpl_path.is_absolute():
            tpl_path = Path(settings.BASE_DIR) / tpl_path

        template_rows = _load_template_rows(tpl_path)

        internos = sorted({r.interno for r in template_rows})
        existentes = {c.interno: c for c in Colectivo.objects.filter(interno__in=internos)}
        missing = [i for i in internos if i not in existentes]
        if missing:
            raise CommandError(
                "Faltan colectivos para estos internos (cargalos primero en Flota > Unidades): "
                + ", ".join(map(str, missing))
            )

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY RUN: no se escribirán cambios"))

        # Overwrite opcional: solo NORMAL, para no borrar especiales multi-día.
        if opts["overwrite"] and not opts["dry_run"]:
            range_start, _ = _day_bounds(start_day)
            _, range_end = _day_bounds(start_day + timedelta(days=days - 1))
            deleted, _ = SalidaProgramada.objects.filter(
                salida_programada__gte=range_start,
                salida_programada__lt=range_end,
                tipo=SalidaProgramada.Tipo.NORMAL,
            ).delete()
            self.stdout.write(f"Se borraron {deleted} salidas NORMAL del rango para regenerar.")

        created = 0
        skipped = 0

        for d in (start_day + timedelta(days=i) for i in range(days)):
            day_start, day_end = _day_bounds(d)

            # Claves existentes para no pisar operación ya cargada.
            existing_keys = set(
                SalidaProgramada.objects.filter(salida_programada__gte=day_start, salida_programada__lt=day_end)
                .values_list("seccion", "salida_label")
            )

            for r in template_rows:
                salida_dt = _make_aware(datetime.combine(d, r.salida_hora))

                llegada_dt = None
                if r.llegada_hora:
                    llegada_day = d
                    # Si la llegada es "menor" que la salida, asumimos vuelta al día siguiente.
                    if r.llegada_hora < r.salida_hora:
                        llegada_day = d + timedelta(days=1)
                    llegada_dt = _make_aware(datetime.combine(llegada_day, r.llegada_hora))

                key = (r.seccion, r.salida_label)
                if key in existing_keys:
                    skipped += 1
                    continue

                sp = SalidaProgramada(
                    colectivo=existentes[r.interno],
                    salida_programada=salida_dt,
                    llegada_programada=llegada_dt,
                    tipo=r.tipo,
                    estado=r.estado,
                    seccion=r.seccion,
                    salida_label=r.salida_label,
                    regreso=r.regreso,
                    chofer=r.chofer,
                    recorrido=r.recorrido,
                    nota=r.nota,
                )

                if not opts["dry_run"]:
                    sp.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(f"OK: creadas {created} salidas. Omitidas por existir: {skipped}."))
        self.stdout.write(
            "Sugerencia: abrir /flota/salidas/?fecha="
            + start_day.isoformat()
            + " y verificar que el diagrama del día ya aparece." 
        )
