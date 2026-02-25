from __future__ import annotations

"""
flota.informe_views

Informe operativo de flota (para el inicio de turno y toma de decisiones del diagramador).

Objetivo
- Resumir en una sola pantalla el estado de las unidades:
  - Salidas próximas
  - Partes abiertos / en proceso (alertas)
  - Vencimientos (VTV / matafuegos) para anticipar problemas
  - Carga de choferes (conteo de salidas por chofer en el día)

Notas
- No se bloquea nada: se informa.
- Offline-first: sin dependencias externas.
"""

from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.shortcuts import render
from django.utils import timezone

from .models import Colectivo, SalidaProgramada
from .partes_models import ParteDiario


def _parse_day(value: str | None):
    if value:
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            return timezone.localdate()
    return timezone.localdate()


def _day_bounds(day):
    start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
    end = start + timedelta(days=1)
    return start, end


def _days_to(d):
    if not d:
        return None
    today = timezone.localdate()
    try:
        return (d - today).days
    except Exception:
        return None


@login_required
def informe_flota(request):
    """
    Pantalla de informe general (operativa):
    - Una tabla por unidad con: próxima salida, partes abiertos, vencimientos.
    - Una tabla de carga por chofer (cantidad de salidas en el día).
    """

    day = _parse_day(request.GET.get("fecha"))
    start, end = _day_bounds(day)

    now = timezone.localtime(timezone.now())
    horizon_hours = int(request.GET.get("hours") or 12)
    horizon_end = now + timedelta(hours=horizon_hours)

    # Salidas próximas (ventana operativa)
    salidas_proximas = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=now, salida_programada__lte=horizon_end)
        .order_by("salida_programada", "colectivo__interno")
    )

    # Salidas del día (para carga por chofer)
    salidas_dia = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=start, salida_programada__lt=end)
        .order_by("salida_programada", "colectivo__interno")
    )

    # Partes abiertos/en proceso por unidad
    partes_abiertos = (
        ParteDiario.objects.filter(estado__in=[ParteDiario.Estado.ABIERTO, ParteDiario.Estado.EN_PROCESO])
        .values("colectivo_id")
        .annotate(
            cant=Count("id"),
            max_severidad=Max("severidad"),
        )
    )
    partes_map = {p["colectivo_id"]: p for p in partes_abiertos}

    # Próxima salida por unidad (en las próximas 48h, para contexto)
    next48 = now + timedelta(hours=48)
    prox_por_unidad = (
        SalidaProgramada.objects.filter(salida_programada__gte=now, salida_programada__lte=next48)
        .values("colectivo_id")
        .annotate(next_dt=Max("salida_programada"))
    )
    # Nota: usamos Max en el queryset agregado; luego ajustamos con una búsqueda real por min.
    # Para evitar dos queries por unidad, hacemos un segundo paso con un map por unidad:
    prox_min_map = {}
    qs = (
        SalidaProgramada.objects.filter(salida_programada__gte=now, salida_programada__lte=next48)
        .values("colectivo_id", "salida_programada")
        .order_by("colectivo_id", "salida_programada")
    )
    for row in qs:
        cid = row["colectivo_id"]
        if cid not in prox_min_map:
            prox_min_map[cid] = row["salida_programada"]

    unidades = Colectivo.objects.filter(is_active=True).order_by("interno")

    # Carga por chofer (conteo simple)
    carga_chofer = defaultdict(int)
    for s in salidas_dia:
        if s.chofer:
            carga_chofer[s.chofer.strip().upper()] += 1

    carga_chofer_rows = [{"chofer": k, "salidas": v} for k, v in sorted(carga_chofer.items(), key=lambda x: (-x[1], x[0]))]

    rows = []
    for u in unidades:
        p = partes_map.get(u.id)
        rows.append(
            {
                "unidad": u,
                "partes_cant": p["cant"] if p else 0,
                "partes_sev": p["max_severidad"] if p else "",
                "next_salida": prox_min_map.get(u.id),
                "vtv_dias": _days_to(getattr(u, "revision_tecnica_vto", None)),
                "matafuego_dias": _days_to(getattr(u, "matafuego_vto", None)),
            }
        )

    ctx = {
        "fecha": day,
        "hours": horizon_hours,
        "salidas_proximas": salidas_proximas,
        "rows": rows,
        "carga_chofer": carga_chofer_rows,
    }
    return render(request, "flota/informe_flota.html", ctx)
