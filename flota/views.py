from __future__ import annotations

from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db.models import Count, Sum, Value, DecimalField, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from tablib import Dataset

from .models import Colectivo
from .forms import ColectivoForm
from .filters import ColectivoFilter
from .resources import ColectivoResource

from inventario.models import MovimientoStock


QTY_FIELD = DecimalField(max_digits=12, decimal_places=3)
ZERO_QTY = Value(0, output_field=QTY_FIELD)


def _badge_por_dias(dias: int | None, sin_fecha_text: str = "Sin fecha"):
    if dias is None:
        return ("info", sin_fecha_text)

    if dias < 0:
        return ("critical", "Vencido")
    if dias == 0:
        return ("critical", "Hoy")
    if 1 <= dias <= 7:
        return ("high", "Por vencer")
    return ("ok", "OK")


def _km_mantenimiento(odometro_km, ultimo_km, intervalo_km):
    """
    Devuelve dict con estado por KM.
    Si falta algún dato -> estado info.
    """
    if not odometro_km or not ultimo_km or not intervalo_km:
        return {
            "badge": "info",
            "estado": "Sin datos",
            "odometro_km": odometro_km,
            "ultimo_km": ultimo_km,
            "intervalo_km": intervalo_km,
            "proximo_km": None,
            "faltan_km": None,
        }

    proximo = int(ultimo_km) + int(intervalo_km)
    faltan = int(proximo) - int(odometro_km)

    if faltan <= 0:
        badge = "critical"
        estado = "Vencido"
    elif faltan <= 500:
        badge = "high"
        estado = "Por vencer"
    elif faltan <= 1500:
        badge = "info"
        estado = "Próximo"
    else:
        badge = "ok"
        estado = "OK"

    return {
        "badge": badge,
        "estado": estado,
        "odometro_km": int(odometro_km),
        "ultimo_km": int(ultimo_km),
        "intervalo_km": int(intervalo_km),
        "proximo_km": int(proximo),
        "faltan_km": int(faltan),
    }


class ColectivoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Colectivo
    template_name = "flota/colectivo_list.html"
    paginate_by = 20
    permission_required = "flota.view_colectivo"

    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = ColectivoFilter(self.request.GET, queryset=qs)
        return self.filterset.qs.order_by("interno")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filterset"] = self.filterset
        ctx["today"] = timezone.localdate()
        return ctx


class ColectivoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Colectivo
    form_class = ColectivoForm
    template_name = "flota/colectivo_form.html"
    permission_required = "flota.add_colectivo"

    def get_success_url(self):
        return reverse("flota:colectivo_list")


class ColectivoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Colectivo
    form_class = ColectivoForm
    template_name = "flota/colectivo_form.html"
    permission_required = "flota.change_colectivo"

    def get_success_url(self):
        return reverse("flota:colectivo_list")


class ColectivoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Colectivo
    template_name = "flota/colectivo_confirm_delete.html"
    permission_required = "flota.delete_colectivo"

    def get_success_url(self):
        return reverse("flota:colectivo_list")


class ColectivoReportView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Colectivo
    template_name = "flota/colectivo_report_30d.html"
    permission_required = "flota.view_colectivo"
    context_object_name = "c"

    def _clamp_days(self, raw: str) -> int:
        try:
            n = int(raw)
        except Exception:
            return 30
        return max(1, min(365, n))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        c: Colectivo = self.object

        days = self._clamp_days(self.request.GET.get("days", "30"))
        dt_from = timezone.now() - timedelta(days=days)
        today = timezone.localdate()

        can_view_inv = self.request.user.has_perm("inventario.view_movimientostock")

        mov_qs = MovimientoStock.objects.none()
        stats_by_tipo = []
        top_consumos = []
        dias_con_actividad = 0
        total_mov = 0

        if can_view_inv:
            interno = str(c.interno)
            dominio = (c.dominio or "").strip().upper()

            tokens = [
                f"INT-{interno}",
                f"INT {interno}",
                f"INTERNO {interno}",
                f"COLECTIVO {interno}",
                f"COLECTIVO-{interno}",
                f"#{interno}",
            ]
            if dominio:
                tokens.append(dominio)
                tokens.append(f"DOM-{dominio}")

            text_q = Q()
            for t in tokens:
                text_q |= Q(referencia__icontains=t) | Q(observaciones__icontains=t)

            link_q = Q(colectivo_id=c.id) | text_q

            mov_qs = (
                MovimientoStock.objects
                .filter(fecha__gte=dt_from)
                .filter(link_q)
                .select_related("producto", "ubicacion", "ubicacion_destino", "usuario", "proveedor", "colectivo")
                .order_by("-fecha", "-id")
            )

            total_mov = mov_qs.count()
            dias_con_actividad = mov_qs.datetimes("fecha", "day").count()

            stats_by_tipo = list(
                mov_qs.values("tipo").annotate(
                    cnt=Count("id"),
                    qty=Coalesce(Sum("cantidad"), ZERO_QTY, output_field=QTY_FIELD),
                ).order_by("tipo")
            )

            top_consumos = list(
                mov_qs.filter(tipo=MovimientoStock.Tipo.EGRESO)
                .values("producto__codigo", "producto__nombre")
                .annotate(qty=Coalesce(Sum("cantidad"), ZERO_QTY, output_field=QTY_FIELD))
                .order_by("-qty", "producto__codigo")[:10]
            )

        # VTV
        vto_vtv = c.revision_tecnica_vto
        vtv_dias = (vto_vtv - today).days if vto_vtv else None
        vtv_badge, vtv_estado = _badge_por_dias(vtv_dias, sin_fecha_text="Sin fecha")

        # Matafuego
        vto_mf = c.matafuego_vto
        mf_dias = (vto_mf - today).days if vto_mf else None
        mf_badge, mf_estado = _badge_por_dias(mf_dias, sin_fecha_text="Sin fecha")

        # Mantenimiento por KM
        aceite = _km_mantenimiento(c.odometro_km, c.aceite_ultimo_cambio_km, c.aceite_intervalo_km)
        filtros = _km_mantenimiento(c.odometro_km, c.filtros_ultimo_cambio_km, c.filtros_intervalo_km)

        # Limpieza (simple)
        if c.limpieza_ultima_fecha:
            dias_limp = (today - c.limpieza_ultima_fecha).days
            if dias_limp <= 1:
                limp_badge, limp_estado = ("ok", "Reciente")
            elif dias_limp <= 7:
                limp_badge, limp_estado = ("high", f"Hace {dias_limp} días")
            else:
                limp_badge, limp_estado = ("critical", f"Hace {dias_limp} días")
        else:
            dias_limp = None
            limp_badge, limp_estado = ("info", "Sin dato")

        ctx.update({
            "days": days,
            "desde": dt_from,
            "can_view_inv": can_view_inv,

            "vtv_badge": vtv_badge,
            "vtv_estado": vtv_estado,
            "vtv_dias": vtv_dias,

            "mf_badge": mf_badge,
            "mf_estado": mf_estado,
            "mf_dias": mf_dias,

            "aceite": aceite,
            "aceite_fecha": c.aceite_ultimo_cambio_fecha,
            "aceite_obs": c.aceite_obs,

            "filtros": filtros,
            "filtros_fecha": c.filtros_ultimo_cambio_fecha,
            "filtros_obs": c.filtros_obs,

            "odometro_km": c.odometro_km,
            "odometro_fecha": c.odometro_fecha,

            "limp_badge": limp_badge,
            "limp_estado": limp_estado,
            "limp_dias": dias_limp,
            "limp_fecha": c.limpieza_ultima_fecha,
            "limp_por": c.limpieza_realizada_por,
            "limp_obs": c.limpieza_obs,

            "mov_qs": mov_qs[:200],
            "total_mov": total_mov,
            "dias_con_actividad": dias_con_actividad,
            "stats_by_tipo": stats_by_tipo,
            "top_consumos": top_consumos,
            "next_url": self.request.get_full_path(),
        })
        return ctx


@login_required
@permission_required("flota.can_export_colectivos", raise_exception=True)
def colectivos_export_csv(request):
    resource = ColectivoResource()
    dataset = resource.export(Colectivo.objects.all().order_by("interno"))
    csv_bytes = dataset.csv.encode("utf-8")

    resp = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="colectivos_export.csv"'
    return resp


@login_required
@permission_required("flota.can_import_colectivos", raise_exception=True)
def colectivos_import_csv(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "No se seleccionó ningún archivo.")
            return redirect("flota:colectivo_import")

        raw = file.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "El archivo no está en UTF-8. Guardalo como UTF-8 y reintentá.")
            return redirect("flota:colectivo_import")

        dataset = Dataset().load(text, format="csv")
        resource = ColectivoResource()

        result = resource.import_data(dataset, dry_run=True, raise_errors=False)
        if result.has_errors():
            messages.error(request, "El archivo tiene errores. Revisá columnas/formatos.")
            pretty = []
            for row_idx, row_errs in result.row_errors():
                pretty.append({"row": row_idx, "errors": [str(e.error) for e in row_errs]})
            return render(request, "flota/colectivo_import.html", {"preview_errors": pretty})

        resource.import_data(dataset, dry_run=False, raise_errors=False)
        messages.success(request, "Importación realizada correctamente.")
        return redirect("flota:colectivo_list")

    return render(request, "flota/colectivo_import.html")