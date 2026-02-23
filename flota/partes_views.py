from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import ListView, CreateView, DetailView

from .models import ParteDiario, ParteDiarioAdjunto
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

        colectivo_id = self.kwargs.get("colectivo_id")
        if colectivo_id:
            qs = qs.filter(colectivo_id=colectivo_id)

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
        ctx["tipos"] = ParteDiario.Tipo.choices
        ctx["estados"] = ParteDiario.Estado.choices
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