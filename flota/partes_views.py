from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import ListView, CreateView, DetailView

from .models import ParteDiario, ParteDiarioAdjunto, Colectivo, SalidaProgramada
from .partes_forms import ParteDiarioForm, ParteDiarioAdjuntoForm


def _clamp_days(raw: str) -> int:
    try:
        n = int(raw)
    except Exception:
        return 30
    return max(1, min(365, n))


class ParteDiarioListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ParteDiario
    template_name = "flota/parte_list.html"
    context_object_name = "items"
    paginate_by = 25
    permission_required = "flota.view_partediario"

    def get_queryset(self):
        qs = super().get_queryset().select_related("colectivo", "reportado_por")

        days = _clamp_days(self.request.GET.get("days", "30"))
        dt_from = timezone.now() - timedelta(days=days)
        qs = qs.filter(fecha_evento__gte=dt_from)

        # Filtro por unidad:
        # - Si viene por URL /colectivos/<id>/partes/, se fuerza ese colectivo.
        # - Si viene por querystring (?colectivo=<id>), se aplica en /partes/.
        colectivo_id = self.kwargs.get("colectivo_id")
        if colectivo_id:
            qs = qs.filter(colectivo_id=colectivo_id)
        else:
            col_raw = (self.request.GET.get("colectivo") or "").strip()
            try:
                if col_raw:
                    qs = qs.filter(colectivo_id=int(col_raw))
            except Exception:
                pass

        tipo = (self.request.GET.get("tipo") or "").strip().upper()
        if tipo and tipo in {k for k, _ in ParteDiario.Tipo.choices}:
            qs = qs.filter(tipo=tipo)

        estado = (self.request.GET.get("estado") or "").strip().upper()
        if estado and estado in {k for k, _ in ParteDiario.Estado.choices}:
            qs = qs.filter(estado=estado)

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(descripcion__icontains=q)
                | Q(observaciones__icontains=q)
                | Q(colectivo__interno__icontains=q)
                | Q(colectivo__dominio__icontains=q)
            )

        return qs.order_by("-fecha_evento", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["days"] = _clamp_days(self.request.GET.get("days", "30"))
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        ctx["tipo"] = (self.request.GET.get("tipo") or "").strip().upper()
        ctx["estado"] = (self.request.GET.get("estado") or "").strip().upper()
        ctx["colectivo_id"] = self.kwargs.get("colectivo_id")
        ctx["colectivo"] = (self.request.GET.get("colectivo") or "").strip()
        ctx["tipos"] = ParteDiario.Tipo.choices
        ctx["estados"] = ParteDiario.Estado.choices

        # Listas para filtros y accesos rápidos (mobile-first)
        ctx["colectivos"] = list(
            Colectivo.objects.filter(is_active=True)
            .only("id", "interno", "dominio")
            .order_by("interno")
        )
        ctx["colectivos_quick"] = ctx["colectivos"][:12]

        # KPIs simples del resultado filtrado (no solo la página actual)
        qs_stats = self.get_queryset()
        stats = qs_stats.aggregate(
            total=Count("id"),
            abiertos=Count("id", filter=Q(estado=ParteDiario.Estado.ABIERTO)),
            en_proceso=Count("id", filter=Q(estado=ParteDiario.Estado.EN_PROCESO)),
            resueltos=Count("id", filter=Q(estado=ParteDiario.Estado.RESUELTO)),
            incidencias=Count("id", filter=Q(tipo=ParteDiario.Tipo.INCIDENCIA)),
            controles=Count("id", filter=Q(tipo=ParteDiario.Tipo.CHECKLIST)),
            mantenimientos=Count("id", filter=Q(tipo=ParteDiario.Tipo.MANTENIMIENTO)),
            auxilios=Count("id", filter=Q(tipo=ParteDiario.Tipo.AUXILIO)),
        )
        ctx["stats"] = stats

        # Unidad seleccionada (para mostrar en UI)
        selected_id = None
        if ctx.get("colectivo_id"):
            selected_id = int(ctx["colectivo_id"])
        else:
            try:
                if ctx.get("colectivo"):
                    selected_id = int(ctx["colectivo"])
            except Exception:
                selected_id = None

        ctx["colectivo_selected"] = None
        if selected_id:
            try:
                ctx["colectivo_selected"] = Colectivo.objects.only("id", "interno", "dominio").get(pk=selected_id)
            except Exception:
                ctx["colectivo_selected"] = None

        return ctx


class ParteDiarioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ParteDiario
    form_class = ParteDiarioForm
    template_name = "flota/parte_form.html"
    permission_required = "flota.add_partediario"

    def get_initial(self):
        initial = super().get_initial()

        col_raw = self.request.GET.get("colectivo") or self.request.GET.get("colectivo_id")
        try:
            if col_raw:
                initial["colectivo"] = int(col_raw)
        except Exception:
            pass

        tipo = (self.request.GET.get("tipo") or "").strip().upper()
        if tipo in {k for k, _ in ParteDiario.Tipo.choices}:
            initial["tipo"] = tipo

        # default: ahora (en localtime, el input datetime-local usa local)
        initial["fecha_evento"] = timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M")

        return initial

    def get_success_url(self):
        next_url = (self.request.POST.get("next") or self.request.GET.get("next") or "").strip()
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse("flota:parte_detail", args=[self.object.pk])

    def form_valid(self, form):
        try:
            with transaction.atomic():
                form.instance.reportado_por = self.request.user
                resp = super().form_valid(form)
                messages.success(self.request, "Parte diario registrado correctamente.")
                return resp
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class ParteDiarioDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ParteDiario
    template_name = "flota/parte_detail.html"
    context_object_name = "p"
    permission_required = "flota.view_partediario"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["adj_form"] = ParteDiarioAdjuntoForm()
        return ctx


@login_required
@permission_required("flota.change_partediario", raise_exception=True)
def parte_adjunto_add(request, pk: int):
    parte = get_object_or_404(ParteDiario, pk=pk)

    if request.method != "POST":
        return redirect("flota:parte_detail", pk=parte.pk)

    form = ParteDiarioAdjuntoForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "No se pudo subir el archivo. Revisá el formulario.")
        return redirect("flota:parte_detail", pk=parte.pk)

    adj = form.save(commit=False)
    adj.parte = parte
    adj.save()

    messages.success(request, "Adjunto subido correctamente.")
    return redirect("flota:parte_detail", pk=parte.pk)


@login_required
@permission_required("flota.change_partediario", raise_exception=True)
def parte_adjunto_delete(request, pk: int, adj_id: int):
    parte = get_object_or_404(ParteDiario, pk=pk)
    adj = get_object_or_404(ParteDiarioAdjunto, pk=adj_id, parte=parte)

    if request.method == "POST":
        # borrar archivo físico y registro
        try:
            adj.archivo.delete(save=False)
        except Exception:
            pass
        adj.delete()
        messages.success(request, "Adjunto eliminado.")
    return redirect("flota:parte_detail", pk=parte.pk)
@login_required
@permission_required("flota.view_partediario", raise_exception=True)
def tv_taller(request):
    """Pantalla TV (Taller): partes abiertos/en proceso priorizados por próxima salida.

    Objetivo operativo:
    - El taller NO usa celulares.
    - En una pantalla grande se debe ver qué unidad requiere atención primero.

    Regla de orden:
    1) Unidades con salida programada dentro de las próximas `hours` horas (más cercana primero).
    2) Luego el resto (sin salida en rango), ordenado por severidad y recencia.

    Parámetros (querystring):
    - hours: horizonte de salidas a considerar (default 12)
    - refresh: segundos de recarga automática (default 20)
    - days: antigüedad máxima de partes a mostrar (default 30)
    """
    # --------- parámetros robustos ----------
    def _int_param(key: str, default: int, lo: int, hi: int) -> int:
        raw = request.GET.get(key, str(default))
        try:
            n = int(raw)
        except Exception:
            n = default
        return max(lo, min(hi, n))

    hours = _int_param("hours", 12, 1, 72)
    refresh_sec = _int_param("refresh", 20, 5, 300)
    days = _int_param("days", 30, 1, 365)
    limit = _int_param("limit", 30, 10, 200)

    now = timezone.now()
    dt_from = now - timedelta(days=days)
    dt_to = now + timedelta(hours=hours)

    # --------- salidas próximas por colectivo (mapa) ----------
    # Elegimos la salida programada más próxima por unidad dentro del rango.
    salidas_qs = (
        SalidaProgramada.objects.filter(
            salida_programada__gte=now,
            salida_programada__lte=dt_to,
        )
        .exclude(estado=SalidaProgramada.Estado.CANCELADA)
        .select_related("colectivo")
        .order_by("colectivo_id", "salida_programada")
    )

    next_salida = {}
    next_salida_label = {}
    next_salida_seccion = {}

    for s in salidas_qs:
        if s.colectivo_id in next_salida:
            continue
        next_salida[s.colectivo_id] = s.salida_programada
        # Para TV: preferimos label del diagrama. Si no hay, usamos hora simple.
        next_salida_label[s.colectivo_id] = (s.salida_label or "").strip()
        next_salida_seccion[s.colectivo_id] = (s.seccion or "").strip()

    # --------- partes abiertos/en proceso ----------
    abiertos = (
        ParteDiario.objects.filter(
            fecha_evento__gte=dt_from,
            estado__in=[ParteDiario.Estado.ABIERTO, ParteDiario.Estado.EN_PROCESO],
        )
        .select_related("colectivo", "reportado_por")
    )

    # Ranking severidad para ordenar (CRITICA primero)
    sev_rank = {
        ParteDiario.Severidad.CRITICA: 4,
        ParteDiario.Severidad.ALTA: 3,
        ParteDiario.Severidad.MEDIA: 2,
        ParteDiario.Severidad.BAJA: 1,
    }

    items = list(abiertos)
    for it in items:
        it.next_dt = next_salida.get(it.colectivo_id)  # datetime or None
        it.next_label = next_salida_label.get(it.colectivo_id, "")
        it.next_seccion = next_salida_seccion.get(it.colectivo_id, "")
        it.sev_rank = sev_rank.get(it.severidad, 0)

    far = now + timedelta(days=3650)
    items.sort(
        key=lambda x: (
            0 if x.next_dt else 1,
            x.next_dt or far,
            -x.sev_rank,
            -int(x.fecha_evento.timestamp()),
            -x.id,
        )
    )
    
    # En TV queremos pocas líneas y muy legibles.
    # Limitamos para no saturar la pantalla.
    items = items[:limit]

    context = {
        "now": now,
        "hours": hours,
        "refresh_sec": refresh_sec,
        "days": days,
        "items": items,
        "limit": limit,
    }
    
    if request.GET.get("partial") == "1":
        return render(request, "flota/_tv_taller_rows.html", context)
    return render(request, "flota/tv_taller.html", context)
