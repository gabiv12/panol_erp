from __future__ import annotations

"""
flota.salidas_views

Este módulo concentra el "Diagrama / Horarios" (Salidas programadas y viajes especiales).

Objetivo operativo
- Carga rápida del diagrama del día (normalmente se arma el día anterior a la tarde/noche).
- Visualización en Pantalla TV (sin depender de teléfonos en taller).
- Impresión del diagrama del día (similar a la planilla en papel).

Notas de diseño (importante para mantenimiento)
- No se usan dependencias externas (offline-first).
- Se prioriza robustez y simplicidad sobre "features" complejas.
- Si más adelante se implementa "Diagramas por patrón" (semanal), este módulo sirve como base.
"""

from datetime import datetime, timedelta, time as dtime

from django.contrib import messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import models
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import SalidaProgramadaForm, SalidaProgramadaBulkForm
from .models import Colectivo, SalidaProgramada
from .partes_models import ParteDiario


# ---------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------
def _parse_day(value: str | None) -> datetime.date:
    """Parsea una fecha YYYY-MM-DD. Si falla, usa la fecha local actual."""
    if value:
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            return timezone.localdate()
    return timezone.localdate()


def _day_bounds(day: datetime.date):
    """Devuelve (start, end) aware para filtrar por día."""
    start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
    end = start + timedelta(days=1)
    return start, end


def _day_has_salidas(day: datetime.date) -> bool:
    start, end = _day_bounds(day)
    return SalidaProgramada.objects.filter(salida_programada__gte=start, salida_programada__lt=end).exists()


def _latest_day_with_salidas() -> datetime.date | None:
    last = SalidaProgramada.objects.order_by("-salida_programada").values_list("salida_programada", flat=True).first()
    if not last:
        return None
    try:
        dt_last = timezone.localtime(last)
        return dt_last.date()
    except Exception:
        return None


def _default_day_for_diagramador() -> datetime.date:
    """
    Heurística operativa robusta (evita pantallas vacías):
    - Preferido:
        - >=18hs: mañana
        - <18hs: hoy
    - Si el día preferido NO tiene salidas y el usuario NO eligió fecha:
        - cae al último día que tenga salidas (si existe).
    """
    now = timezone.localtime(timezone.now())
    base = timezone.localdate()
    preferred = base + timedelta(days=1) if now.hour >= 18 else base

    if _day_has_salidas(preferred):
        return preferred

    last = _latest_day_with_salidas()
    return last or preferred


def _resolve_day_from_request(request) -> tuple[datetime.date, bool]:
    """
    Devuelve (day, explicit):
    - explicit=True si el usuario eligió ?fecha=YYYY-MM-DD
    - explicit=False si usamos default.
    """
    fecha = (request.GET.get("fecha") or "").strip()
    if fecha:
        day = _parse_day(fecha)
        return day, True
    return _default_day_for_diagramador(), False


def _resolve_day_for_views(request, preferred: datetime.date) -> datetime.date:
    """
    Si el usuario NO eligió fecha y el día preferido está vacío, cae al último día con salidas.
    """
    day, explicit = _resolve_day_from_request(request)
    if explicit:
        return day
    return day or preferred




def _salidas_datalists():
    """
    Devuelve listas para autocompletar (datalist HTML) sin crear catálogos extra.
    Evita que el diagramador tenga que escribir siempre lo mismo.
    """
    return {
        "datalist_choferes": list(
            SalidaProgramada.objects.exclude(chofer="")
            .values_list("chofer", flat=True)
            .distinct()
            .order_by("chofer")[:300]
        ),
        "datalist_secciones": list(
            SalidaProgramada.objects.exclude(seccion="")
            .values_list("seccion", flat=True)
            .distinct()
            .order_by("seccion")[:300]
        ),
        "datalist_recorridos": list(
            SalidaProgramada.objects.exclude(recorrido="")
            .values_list("recorrido", flat=True)
            .distinct()
            .order_by("recorrido")[:300]
        ),
        "datalist_etiquetas": list(
            SalidaProgramada.objects.exclude(salida_label="")
            .values_list("salida_label", flat=True)
            .distinct()
            .order_by("salida_label")[:300]
        ),
        "datalist_regresos": list(
            SalidaProgramada.objects.exclude(regreso="")
            .values_list("regreso", flat=True)
            .distinct()
            .order_by("regreso")[:300]
        ),
    }


def _snapshot_salida(s: SalidaProgramada) -> dict:
    """Snapshot consistente (serializable) para auditoría de cambios."""
    def dt(v):
        return v.isoformat() if v else None

    return {
        "colectivo_id": s.colectivo_id,
        "salida_programada": dt(s.salida_programada),
        "llegada_programada": dt(s.llegada_programada),
        "tipo": s.tipo,
        "estado": s.estado,
        "seccion": (s.seccion or ""),
        "salida_label": (s.salida_label or ""),
        "regreso": (s.regreso or ""),
        "chofer": (s.chofer or ""),
        "recorrido": (s.recorrido or ""),
        "nota": (s.nota or ""),
    }


def _diff_salida(before: SalidaProgramada, after: SalidaProgramada) -> dict | None:
    """Devuelve {campo: {before, after}} solo con los campos modificados."""
    b = _snapshot_salida(before)
    a = _snapshot_salida(after)
    changes = {}
    for k in a.keys():
        if b.get(k) != a.get(k):
            changes[k] = {"before": b.get(k), "after": a.get(k)}
    return changes or None


def _log_salida_change(request, salida: SalidaProgramada, changes: dict) -> None:
    """Registra constancia de cambios usando django.contrib.admin.LogEntry."""
    try:
        ct = ContentType.objects.get_for_model(SalidaProgramada)
        LogEntry.objects.log_action(
            user_id=getattr(request.user, "id", None) or 1,
            content_type_id=ct.pk,
            object_id=str(salida.pk),
            object_repr=str(salida),
            action_flag=CHANGE,
            change_message={"fields": list(changes.keys()), "changes": changes},
        )
    except Exception:
        return


# ---------------------------------------------------------------------
# CRUD / Listado
# ---------------------------------------------------------------------
class SalidaProgramadaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "flota.view_salidaprogramada"
    template_name = "flota/salida_list.html"
    context_object_name = "salidas"
    paginate_by = 80

    def get_queryset(self):
        qs = SalidaProgramada.objects.select_related("colectivo")

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                (models.Q(colectivo__dominio__icontains=q))
                | (models.Q(colectivo__interno__icontains=q))
                | (models.Q(chofer__icontains=q))
                | (models.Q(seccion__icontains=q))
                | (models.Q(salida_label__icontains=q))
                | (models.Q(regreso__icontains=q))
                | (models.Q(recorrido__icontains=q))
                | (models.Q(nota__icontains=q))
            )

        # Fecha (por defecto: heurística robusta)
        day, _explicit = _resolve_day_from_request(self.request)

        start, end = _day_bounds(day)
        qs = qs.filter(salida_programada__gte=start, salida_programada__lt=end)

        return qs.order_by("salida_programada", "id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        day, _explicit = _resolve_day_from_request(self.request)
        ctx["fecha"] = str(day)
        try:
            ct = ContentType.objects.get_for_model(SalidaProgramada)
            ctx["salida_log"] = (
                LogEntry.objects.filter(content_type=ct, object_id=str(self.object.pk))
                .order_by("-action_time")[:10]
            )
        except Exception:
            ctx["salida_log"] = []
        return ctx


class SalidaProgramadaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "flota.add_salidaprogramada"
    model = SalidaProgramada
    form_class = SalidaProgramadaForm
    template_name = "flota/salida_form.html"
    success_url = reverse_lazy("flota:salida_list")

    def get_initial(self):
        initial = super().get_initial()

        # Si viene la fecha desde la lista, preconfiguramos un horario razonable (05:00)
        fecha = (self.request.GET.get("fecha") or "").strip()
        day = _parse_day(fecha) if fecha else _default_day_for_diagramador()
        initial.setdefault("salida_programada", timezone.make_aware(datetime.combine(day, dtime(5, 0))))

        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_salidas_datalists())
        day, _explicit = _resolve_day_from_request(self.request)
        ctx["fecha"] = str(day)
        try:
            ct = ContentType.objects.get_for_model(SalidaProgramada)
            ctx["salida_log"] = (
                LogEntry.objects.filter(content_type=ct, object_id=str(self.object.pk))
                .order_by("-action_time")[:10]
            )
        except Exception:
            ctx["salida_log"] = []
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Salida programada creada.")
        return super().form_valid(form)


class SalidaProgramadaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "flota.change_salidaprogramada"
    model = SalidaProgramada
    form_class = SalidaProgramadaForm
    template_name = "flota/salida_form.html"
    success_url = reverse_lazy("flota:salida_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_salidas_datalists())
        day, _explicit = _resolve_day_from_request(self.request)
        ctx["fecha"] = str(day)
        try:
            ct = ContentType.objects.get_for_model(SalidaProgramada)
            ctx["salida_log"] = (
                LogEntry.objects.filter(content_type=ct, object_id=str(self.object.pk))
                .order_by("-action_time")[:10]
            )
        except Exception:
            ctx["salida_log"] = []
        return ctx

    def form_valid(self, form):
        before = SalidaProgramada.objects.get(pk=self.object.pk)
        resp = super().form_valid(form)
        after = self.object
        changes = _diff_salida(before, after)
        if changes:
            _log_salida_change(self.request, after, changes)
        messages.success(self.request, "Salida programada actualizada.")
        return resp


class SalidaProgramadaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "flota.delete_salidaprogramada"
    model = SalidaProgramada
    template_name = "flota/salida_confirm_delete.html"
    success_url = reverse_lazy("flota:salida_list")


# ---------------------------------------------------------------------
# Acciones operativas
# ---------------------------------------------------------------------
@login_required
@permission_required("flota.add_salidaprogramada", raise_exception=True)
@require_POST
def salidas_copiar_dia_anterior(request):
    """
    Copia el diagrama del día anterior a la fecha seleccionada.

    Caso real:
    - El diagramador arma el diagrama a las 19/20hs para el día siguiente.
    - Muchas salidas se repiten y solo se corrigen excepciones.
    """
    fecha = (request.POST.get("fecha") or "").strip()
    if not fecha:
        return HttpResponseBadRequest("Falta fecha")

    try:
        to_day = datetime.fromisoformat(fecha).date()
    except Exception:
        return HttpResponseBadRequest("Fecha inválida")

    from_day = to_day - timedelta(days=1)

    from_start, from_end = _day_bounds(from_day)
    to_start, to_end = _day_bounds(to_day)

    origen = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=from_start, salida_programada__lt=from_end)
        .order_by("salida_programada", "id")
    )

    if not origen.exists():
        messages.warning(request, "No hay salidas el día anterior para copiar.")
        return redirect(f"{reverse_lazy('flota:salida_list')}?fecha={to_day}")

    # Índice para evitar duplicados simples (colectivo + salida_programada exacta)
    existentes = set(
        SalidaProgramada.objects.filter(salida_programada__gte=to_start, salida_programada__lt=to_end)
        .values_list("colectivo_id", "salida_programada")
    )

    created = 0
    delta = timedelta(days=1)

    for s in origen:
        new_dt = s.salida_programada + delta
        if (s.colectivo_id, new_dt) in existentes:
            continue

        obj = SalidaProgramada(
            colectivo=s.colectivo,
            salida_programada=new_dt,
            llegada_programada=(s.llegada_programada + delta) if s.llegada_programada else None,
            tipo=s.tipo,
            estado=SalidaProgramada.Estado.PROGRAMADA,
            seccion=s.seccion,
            salida_label=s.salida_label,
            regreso=s.regreso,
            chofer=s.chofer,
            recorrido=s.recorrido,
            nota=s.nota,
        )
        obj.save()
        created += 1

    if created:
        messages.success(request, f"Copiadas {created} salidas desde {from_day} a {to_day}.")
    else:
        messages.info(request, "No se copiaron salidas (ya existían).")

    return redirect(f"{reverse_lazy('flota:salida_list')}?fecha={to_day}")




@require_POST
@login_required
@permission_required("flota.add_salidaprogramada", raise_exception=True)
def salidas_copiar_15_dias(request):
    """
    Copia el diagrama de un día base a los próximos 15 días (incluye el día base + 14).

    Caso real:
    - Los turnos suelen cambiar cada 15 días.
    - Se arma una "quincena" y luego se ajustan excepciones.
    """
    fecha = (request.POST.get("fecha") or "").strip()
    if not fecha:
        return HttpResponseBadRequest("Falta fecha")

    try:
        base_day = datetime.fromisoformat(fecha).date()
    except Exception:
        return HttpResponseBadRequest("Fecha inválida")

    from_start, from_end = _day_bounds(base_day)

    origen = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=from_start, salida_programada__lt=from_end)
        .order_by("salida_programada", "id")
    )

    if not origen.exists():
        messages.warning(request, "No hay salidas en ese día para copiar.")
        return redirect(f"{reverse_lazy('flota:salida_list')}?fecha={base_day}")

    # Índice para evitar duplicados simples (colectivo + salida_programada exacta)
    rango_start, _ = _day_bounds(base_day)
    rango_end = rango_start + timedelta(days=15)
    existentes = set(
        SalidaProgramada.objects.filter(salida_programada__gte=rango_start, salida_programada__lt=rango_end)
        .values_list("colectivo_id", "salida_programada")
    )

    created = 0
    for day_offset in range(1, 15):
        delta = timedelta(days=day_offset)

        for s in origen:
            new_dt = s.salida_programada + delta
            key = (s.colectivo_id, new_dt)
            if key in existentes:
                continue

            SalidaProgramada.objects.create(
                colectivo=s.colectivo,
                salida_programada=new_dt,
                llegada_programada=(s.llegada_programada + delta) if s.llegada_programada else None,
                tipo=s.tipo,
                estado=SalidaProgramada.Estado.PROGRAMADA,
                seccion=s.seccion,
                salida_label=s.salida_label,
                regreso=s.regreso,
                chofer=s.chofer,
                recorrido=s.recorrido,
                nota=s.nota,
            )
            existentes.add(key)
            created += 1

    if created:
        messages.success(request, f"Copiadas {created} salidas a 15 días desde {base_day}.")
    else:
        messages.info(request, "No se copiaron salidas (ya existían).")

    return redirect(f"{reverse_lazy('flota:salida_list')}?fecha={base_day}")


@login_required
def plan_15_dias(request):
    """
    Planificación por quincena (15 días) en formato de agenda.

    Operación real:
    - El diagrama suele armarse el día anterior a la tarde/noche.
    - Con turnos rotativos, planificar 15 días reduce reprocesos.
    """
    start_str = (request.GET.get("start") or "").strip()
    start_day = _parse_day(start_str) if start_str else _default_day_for_diagramador()
    q = (request.GET.get("q") or "").strip()

    start_dt, _ = _day_bounds(start_day)
    end_dt = start_dt + timedelta(days=15)

    qs = SalidaProgramada.objects.select_related("colectivo").filter(salida_programada__gte=start_dt, salida_programada__lt=end_dt)
    if q:
        qs = qs.filter(
            models.Q(colectivo__interno__icontains=q)
            | models.Q(colectivo__dominio__icontains=q)
            | models.Q(chofer__icontains=q)
            | models.Q(recorrido__icontains=q)
            | models.Q(seccion__icontains=q)
            | models.Q(salida_label__icontains=q)
        )

    salidas = list(qs.order_by("salida_programada", "colectivo__interno", "id"))

    salidas_by_day = {}
    for s in salidas:
        d = timezone.localtime(s.salida_programada).date()
        salidas_by_day.setdefault(d, []).append(s)

    # Partes abiertos/en proceso por unidad (alerta informativa)
    partes = (
        ParteDiario.objects.filter(estado__in=[ParteDiario.Estado.ABIERTO, ParteDiario.Estado.EN_PROCESO])
        .values("colectivo_id")
        .annotate(cant=models.Count("id"))
    )
    partes_map = {p["colectivo_id"]: p["cant"] for p in partes}
    colectivos_con_partes = list(partes_map.keys())

    days = []
    for i in range(15):
        d = start_day + timedelta(days=i)
        days.append({"day": d, "salidas": salidas_by_day.get(d, [])})

    ctx = {"start": start_day, "q": q, "days": days, "colectivos_con_partes": colectivos_con_partes}
    return render(request, "flota/plan_15.html", ctx)


@login_required
def plan_15_print(request):
    """Versión imprimible del plan quincenal (15 días)."""
    start_str = (request.GET.get("start") or "").strip()
    start_day = _parse_day(start_str) if start_str else _default_day_for_diagramador()
    q = (request.GET.get("q") or "").strip()

    start_dt, _ = _day_bounds(start_day)
    end_dt = start_dt + timedelta(days=15)

    qs = SalidaProgramada.objects.select_related("colectivo").filter(salida_programada__gte=start_dt, salida_programada__lt=end_dt)
    if q:
        qs = qs.filter(
            models.Q(colectivo__interno__icontains=q)
            | models.Q(colectivo__dominio__icontains=q)
            | models.Q(chofer__icontains=q)
            | models.Q(recorrido__icontains=q)
            | models.Q(seccion__icontains=q)
            | models.Q(salida_label__icontains=q)
        )

    salidas = list(qs.order_by("salida_programada", "colectivo__interno", "id"))
    salidas_by_day = {}
    for s in salidas:
        d = timezone.localtime(s.salida_programada).date()
        salidas_by_day.setdefault(d, []).append(s)

    days = []
    for i in range(15):
        d = start_day + timedelta(days=i)
        days.append({"day": d, "salidas": salidas_by_day.get(d, [])})

    return render(request, "flota/plan_15_print.html", {"start": start_day, "q": q, "days": days})


@login_required
def plan_15_export_csv(request):
    """Export CSV del plan quincenal (15 días) para control/archivo."""
    import csv
    from django.http import HttpResponse

    start_str = (request.GET.get("start") or "").strip()
    start_day = _parse_day(start_str) if start_str else _default_day_for_diagramador()
    q = (request.GET.get("q") or "").strip()

    start_dt, _ = _day_bounds(start_day)
    end_dt = start_dt + timedelta(days=15)

    qs = SalidaProgramada.objects.select_related("colectivo").filter(salida_programada__gte=start_dt, salida_programada__lt=end_dt)
    if q:
        qs = qs.filter(
            models.Q(colectivo__interno__icontains=q)
            | models.Q(colectivo__dominio__icontains=q)
            | models.Q(chofer__icontains=q)
            | models.Q(recorrido__icontains=q)
            | models.Q(seccion__icontains=q)
            | models.Q(salida_label__icontains=q)
        )

    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="plan_15_{start_day}.csv"'

    w = csv.writer(resp)
    w.writerow(["fecha", "hora", "interno", "dominio", "seccion", "salida_label", "regreso", "chofer", "recorrido", "tipo", "estado", "nota"])

    for s in qs.order_by("salida_programada", "colectivo__interno", "id"):
        w.writerow(
            [
                timezone.localtime(s.salida_programada).date().isoformat(),
                timezone.localtime(s.salida_programada).strftime("%H:%M"),
                s.colectivo.interno,
                s.colectivo.dominio,
                s.seccion,
                s.salida_label,
                s.regreso,
                s.chofer,
                s.recorrido,
                s.tipo,
                s.estado,
                s.nota,
            ]
        )

    return resp


@require_POST
@login_required
@permission_required("flota.add_salidaprogramada", raise_exception=True)
def plan_15_copiar_quincena_anterior(request):
    """
    Copia la quincena anterior (+15 días) hacia la quincena actual.

    Caso real:
    - Los turnos rotativos cambian cada ~15 días.
    - Se parte de lo ya diagramado (quincena anterior) y se ajustan excepciones.
    - Evita duplicados simples (colectivo + salida_programada exacta).
    """
    start_str = (request.POST.get("start") or "").strip()
    if not start_str:
        return HttpResponseBadRequest("Falta start")

    try:
        start_day = datetime.fromisoformat(start_str).date()
    except Exception:
        return HttpResponseBadRequest("Start inválido")

    from_start = start_day - timedelta(days=15)
    to_start = start_day
    to_end = to_start + timedelta(days=15)

    # Índice de existentes en destino (15 días)
    existentes = set(
        SalidaProgramada.objects.filter(salida_programada__gte=_day_bounds(to_start)[0], salida_programada__lt=to_end)
        .values_list("colectivo_id", "salida_programada")
    )

    created = 0
    skipped_days = 0

    # Por cada día de la quincena: copia desde (día-15) a (día)
    for day_offset in range(15):
        src_day = from_start + timedelta(days=day_offset)
        dst_day = to_start + timedelta(days=day_offset)

        src_start, src_end = _day_bounds(src_day)
        origen = (
            SalidaProgramada.objects.select_related("colectivo")
            .filter(salida_programada__gte=src_start, salida_programada__lt=src_end)
            .order_by("salida_programada", "id")
        )
        if not origen.exists():
            skipped_days += 1
            continue

        delta = timedelta(days=15)
        for s in origen:
            new_dt = s.salida_programada + delta
            key = (s.colectivo_id, new_dt)
            if key in existentes:
                continue

            SalidaProgramada.objects.create(
                colectivo=s.colectivo,
                salida_programada=new_dt,
                llegada_programada=(s.llegada_programada + delta) if s.llegada_programada else None,
                tipo=s.tipo,
                estado=SalidaProgramada.Estado.PROGRAMADA,
                seccion=s.seccion,
                salida_label=s.salida_label,
                regreso=s.regreso,
                chofer=s.chofer,
                recorrido=s.recorrido,
                nota=s.nota,
            )
            existentes.add(key)
            created += 1

    if created:
        msg = f"Copiada quincena anterior: {created} salidas creadas."
        if skipped_days:
            msg += f" (Días sin datos en origen: {skipped_days})"
        messages.success(request, msg)
    else:
        messages.info(request, "No se copiaron salidas (ya existían o no había datos en la quincena anterior).")

    return redirect(f"{reverse_lazy('flota:plan_15')}?start={start_day.isoformat()}")


# ---------------------------------------------------------------------
# API mínima (offline) para UX del formulario
# ---------------------------------------------------------------------
@login_required
@require_GET
def api_colectivo_info(request):
    """
    Devuelve un resumen operativo del colectivo:
    - Cantidad de partes ABIERTO/EN_PROCESO
    - Severidad más alta abierta
    - Último parte abierto (resumen corto)

    Se usa en el formulario de salidas para alertar al diagramador, sin bloquear.
    """
    raw_id = (request.GET.get("colectivo_id") or "").strip()
    if not raw_id.isdigit():
        return JsonResponse({"ok": False, "error": "colectivo_id inválido"}, status=400)

    colectivo_id = int(raw_id)

    try:
        c = Colectivo.objects.get(id=colectivo_id)
    except Colectivo.DoesNotExist:
        return JsonResponse({"ok": False, "error": "No existe el colectivo"}, status=404)

    abiertos = ParteDiario.objects.filter(colectivo_id=colectivo_id).exclude(estado=ParteDiario.Estado.RESUELTO)

    total = abiertos.count()

    # Determinar severidad más alta (CRITICA > ALTA > MEDIA > BAJA)
    severidad_rank = {
        ParteDiario.Severidad.CRITICA: 4,
        ParteDiario.Severidad.ALTA: 3,
        ParteDiario.Severidad.MEDIA: 2,
        ParteDiario.Severidad.BAJA: 1,
    }

    top_sev = None
    top_rank = 0
    last = abiertos.order_by("-fecha_evento", "-id").first()

    if last:
        for sev in abiertos.values_list("severidad", flat=True).distinct():
            r = severidad_rank.get(sev, 0)
            if r > top_rank:
                top_rank = r
                top_sev = sev

    return JsonResponse(
        {
            "ok": True,
            "colectivo": {
                "id": c.id,
                "interno": c.interno,
                "dominio": c.dominio,
                "is_active": getattr(c, "is_active", True),
            },
            "partes": {
                "abiertos": total,
                "severidad_max": top_sev,
                "ultimo": (
                    {
                        "fecha": timezone.localtime(last.fecha_evento).isoformat() if last else None,
                        "estado": last.estado if last else None,
                        "severidad": last.severidad if last else None,
                        "resumen": last.resumen if last else None,
                    }
                    if last
                    else None
                ),
            },
        }
    )


# ---------------------------------------------------------------------
# Impresión / Pantalla TV
# ---------------------------------------------------------------------
@login_required
@login_required
@permission_required("flota.change_salidaprogramada", raise_exception=True)
def diagrama_edit(request):
    """Editor rápido del diagrama del día (bulk edit)."""
    day, _explicit = _resolve_day_from_request(request)
    day = day
    start, end = _day_bounds(day)

    qs = (
        SalidaProgramada.objects.filter(salida_programada__gte=start, salida_programada__lt=end)
        .select_related("colectivo")
        .order_by("salida_programada", "id")
    )

    FormSet = modelformset_factory(
        SalidaProgramada,
        form=SalidaProgramadaBulkForm,
        extra=0,
        can_delete=False,
    )

    colectivos_ids = list(qs.values_list("colectivo_id", flat=True).distinct())
    open_partes = (
        ParteDiario.objects.filter(
            colectivo_id__in=colectivos_ids,
            estado__in=[ParteDiario.Estado.ABIERTO, ParteDiario.Estado.EN_PROCESO],
        )
        .order_by("-fecha_evento", "-id")
    )

    parte_pk_by_colectivo = {}
    for p in open_partes:
        if p.colectivo_id not in parte_pk_by_colectivo:
            parte_pk_by_colectivo[p.colectivo_id] = p.pk

    before_map = {s.pk: _snapshot_salida(s) for s in qs}

    if request.method == "POST":
        formset = FormSet(request.POST, queryset=qs)
        if formset.is_valid():
            saved = formset.save()
            for obj in saved:
                before = before_map.get(obj.pk)
                if not before:
                    continue
                after = _snapshot_salida(obj)
                changes = {}
                for k in after.keys():
                    if before.get(k) != after.get(k):
                        changes[k] = {"before": before.get(k), "after": after.get(k)}
                if changes:
                    _log_salida_change(request, obj, changes)

            messages.success(request, "Diagrama actualizado.")
            return redirect(f"{reverse_lazy('flota:salida_diagrama_edit')}?fecha={day.isoformat()}")
        messages.error(request, "No se pudo guardar. Revisá los campos marcados.")
    else:
        formset = FormSet(queryset=qs)

    ctx = {
        "day": day,
        "formset": formset,
        "parte_pk_by_colectivo": parte_pk_by_colectivo,
    }
    ctx.update(_salidas_datalists())
    return render(request, "flota/diagrama_edit.html", ctx)


def diagrama_print(request):
    """Vista imprimible del diagrama del día (similar a la planilla en papel)."""
    day, _explicit = _resolve_day_from_request(request)
    day = day

    start, end = _day_bounds(day)

    salidas = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=start, salida_programada__lt=end)
        .order_by("seccion", "salida_programada", "id")
    )

    # Agrupar por sección
    grupos = {}
    for s in salidas:
        key = (s.seccion or "SIN SECCIÓN").strip()
        grupos.setdefault(key, []).append(s)

    return render(request, "flota/diagrama_print.html", {"day": day, "grupos": grupos})



@login_required
@permission_required("flota.view_salidaprogramada", raise_exception=True)
def salidas_dual(request):
    """
    Vista operativa para diagramador: hoy y mañana en paralelo.
    - Si ?fecha=YYYY-MM-DD => la izquierda es esa fecha y la derecha es +1 día.
    - Si no hay datos, cae al último día con salidas para no quedar vacío.
    """
    base_day, explicit = _resolve_day_from_request(request)
    if (not explicit) and (not _day_has_salidas(base_day)):
        last = _latest_day_with_salidas()
        if last:
            base_day = last

    day_a = base_day
    day_b = base_day + timedelta(days=1)

    start_a, end_a = _day_bounds(day_a)
    start_b, end_b = _day_bounds(day_b)

    salidas_a = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=start_a, salida_programada__lt=end_a)
        .order_by("salida_programada", "id")
    )
    salidas_b = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=start_b, salida_programada__lt=end_b)
        .order_by("salida_programada", "id")
    )

    return render(
        request,
        "flota/salida_dual.html",
        {
            "day_a": day_a,
            "day_b": day_b,
            "salidas_a": salidas_a,
            "salidas_b": salidas_b,
        },
    )


@login_required
def tv_horarios(request):
    """
    Pantalla "TV Horarios" (diagrama por fecha):
    - Por defecto: heurística de diagramador (>=18: mañana).
    - Si ese día no tiene salidas, cae al último día con salidas.
    - Permite override: ?fecha=YYYY-MM-DD
    """
    now = timezone.localtime(timezone.now())

    day, explicit = _resolve_day_from_request(request)
    if (not explicit) and (not _day_has_salidas(day)):
        last = _latest_day_with_salidas()
        if last:
            day = last

    start, end = _day_bounds(day)

    salidas = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=start, salida_programada__lt=end)
        .order_by("salida_programada", "id")
    )

    return render(
        request,
        "flota/tv_horarios.html",
        {
            "salidas": salidas,
            "now": now,
            "day": day,
            "refresh_sec": 20,
        },
    )


# ---------------------------------------------------------------------
# Plantillas operativas (Normal / Domingo)
# ---------------------------------------------------------------------
def _find_source_day_for_plantilla(to_day, modo):
    # Busca hacia atrÃ¡s (hasta 30 dÃ­as) un dÃ­a "modelo" con salidas.
    modo = (modo or "normal").strip().lower()
    for i in range(1, 31):
        d = to_day - timedelta(days=i)
        if modo == "domingo" and d.weekday() != 6:
            continue
        if modo == "normal" and d.weekday() == 6:
            continue

        s, e = _day_bounds(d)
        if SalidaProgramada.objects.filter(salida_programada__gte=s, salida_programada__lt=e).exists():
            return d

    return to_day - timedelta(days=1)


def _copy_salidas_between_days(request, from_day, to_day):
    from_start, from_end = _day_bounds(from_day)
    to_start, to_end = _day_bounds(to_day)

    origen = (
        SalidaProgramada.objects.select_related("colectivo")
        .filter(salida_programada__gte=from_start, salida_programada__lt=from_end)
        .order_by("salida_programada", "id")
    )

    if not origen.exists():
        messages.warning(request, f"No hay salidas el dÃ­a modelo ({from_day}) para copiar.")
        return redirect(f"{reverse_lazy('flota:salida_list')}?fecha={to_day}")

    existentes = set(
        SalidaProgramada.objects.filter(salida_programada__gte=to_start, salida_programada__lt=to_end)
        .values_list("colectivo_id", "salida_programada")
    )

    created = 0
    delta = (to_start - from_start)

    for s in origen:
        new_dt = s.salida_programada + delta
        if (s.colectivo_id, new_dt) in existentes:
            continue

        obj = SalidaProgramada(
            colectivo=s.colectivo,
            salida_programada=new_dt,
            llegada_programada=(s.llegada_programada + delta) if s.llegada_programada else None,
            tipo=s.tipo,
            estado=SalidaProgramada.Estado.PROGRAMADA,
            seccion=s.seccion,
            salida_label=s.salida_label,
            regreso=s.regreso,
            chofer=s.chofer,
            recorrido=s.recorrido,
            nota=s.nota,
        )
        obj.save()
        created += 1

    if created:
        messages.success(request, f"Generadas {created} salidas desde plantilla ({from_day}) a {to_day}.")
    else:
        messages.info(request, "No se generaron salidas (ya existÃ­an).")

    return redirect(f"{reverse_lazy('flota:salida_list')}?fecha={to_day}")


@login_required
@permission_required("flota.add_salidaprogramada", raise_exception=True)
@require_POST
def salidas_generar_desde_plantilla(request):
    fecha = (request.POST.get("fecha") or "").strip()
    modo = (request.POST.get("modo") or "normal").strip().lower()

    if not fecha:
        return HttpResponseBadRequest("Falta fecha")

    try:
        to_day = datetime.fromisoformat(fecha).date()
    except Exception:
        return HttpResponseBadRequest("Fecha invÃ¡lida")

    from_day = _find_source_day_for_plantilla(to_day, modo)
    return _copy_salidas_between_days(request, from_day, to_day)
