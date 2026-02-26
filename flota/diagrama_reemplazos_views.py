from __future__ import annotations

from datetime import datetime, time

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms import modelformset_factory
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import Colectivo, SalidaProgramada
from .partes_models import ParteDiario


def _parse_day(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return timezone.localdate()


def _day_bounds(day):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(day, time.min), tz)
    end = timezone.make_aware(datetime.combine(day, time.max), tz)
    # end inclusive -> usamos < end_next para rangos típicos
    end_next = start + timezone.timedelta(days=1)
    return start, end_next


def _occupied_units_by_special(start, end):
    """Unidades ocupadas por viaje especial que se superpone con [start, end)."""
    qs = (
        SalidaProgramada.objects.filter(
            tipo=SalidaProgramada.Tipo.ESPECIAL,
            llegada_programada__isnull=False,
            salida_programada__lt=end,
            llegada_programada__gte=start,
        )
        .select_related("colectivo")
        .order_by("llegada_programada")
    )
    occ = {}
    for s in qs:
        occ[s.colectivo_id] = {
            "hasta": s.llegada_programada,
            "pk": s.pk,
            "label": (s.salida_label or "").strip(),
            "seccion": (s.seccion or "").strip(),
        }
    return occ


def _open_parte_by_colectivo(colectivo_ids):
    open_partes = (
        ParteDiario.objects.filter(
            colectivo_id__in=colectivo_ids,
            estado__in=[ParteDiario.Estado.ABIERTO, ParteDiario.Estado.EN_PROCESO],
        )
        .order_by("-fecha_evento", "-id")
    )
    mp = {}
    for p in open_partes:
        if p.colectivo_id not in mp:
            mp[p.colectivo_id] = p.pk
    return mp


class _ColectivoField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.occupied_map = kwargs.pop("occupied_map", {})
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj: Colectivo):
        base = f"Interno {obj.interno} - {obj.dominio}"
        info = self.occupied_map.get(obj.pk)
        if info and info.get("hasta"):
            hasta = timezone.localtime(info["hasta"]).strftime("%d/%m %H:%M")
            return f"{base} (OCUPADA: especial hasta {hasta})"
        return base


class SalidaReemplazoForm(forms.ModelForm):
    chofer = forms.CharField(required=False)

    class Meta:
        model = SalidaProgramada
        fields = ["colectivo", "chofer"]

    def __init__(self, *args, **kwargs):
        occupied_map = kwargs.pop("occupied_map", {})
        super().__init__(*args, **kwargs)

        # Colectivo con labels + bloqueo de ocupadas vía clean
        self.fields["colectivo"] = _ColectivoField(
            queryset=Colectivo.objects.all().order_by("interno"),
            occupied_map=occupied_map,
            empty_label=None,
        )
        self.fields["colectivo"].widget.attrs.update({"class": "ti-input"})
        self.fields["chofer"].widget.attrs.update({"class": "ti-input", "list": "dl_choferes", "placeholder": "Ej: APELLIDO, Nombre"})

        self._occupied_ids = set(occupied_map.keys())

    def clean_colectivo(self):
        obj: Colectivo = self.cleaned_data.get("colectivo")
        if not obj:
            return obj

        # Si intenta cambiar a una unidad ocupada por especial, lo bloqueamos.
        if obj.pk in self._occupied_ids and obj.pk != getattr(self.instance, "colectivo_id", None):
            raise forms.ValidationError("Unidad ocupada por viaje especial. Elegí otra unidad.")
        return obj


@login_required
@permission_required("flota.change_salidaprogramada", raise_exception=True)
def diagrama_reemplazos(request):
    """Editor simple del día: solo reemplazos (Unidad + Chofer)."""
    day = _parse_day((request.GET.get("fecha") or "").strip())
    start, end = _day_bounds(day)

    qs = (
        SalidaProgramada.objects.filter(salida_programada__gte=start, salida_programada__lt=end)
        .select_related("colectivo")
        .order_by("salida_programada", "id")
    )

    salidas = list(qs)
    colectivos_ids = list({s.colectivo_id for s in salidas})
    parte_pk_by_colectivo = _open_parte_by_colectivo(colectivos_ids)
    occupied_map = _occupied_units_by_special(start, end)

    # Adjuntar info de alerta por parte (sin dict indexing en template)
    for s in salidas:
        s.open_parte_pk = parte_pk_by_colectivo.get(s.colectivo_id)

    FormSet = modelformset_factory(
        SalidaProgramada,
        form=SalidaReemplazoForm,
        extra=0,
        can_delete=False,
    )

    if request.method == "POST":
        formset = FormSet(request.POST, queryset=qs, form_kwargs={"occupied_map": occupied_map})
        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            messages.success(request, "Reemplazos guardados.")
            return redirect(f"{reverse('flota:salida_diagrama_reemplazos')}?fecha={day.isoformat()}")
        messages.error(request, "No se pudo guardar. Revisá los campos marcados.")
    else:
        formset = FormSet(queryset=qs, form_kwargs={"occupied_map": occupied_map})

    ctx = {
        "day": day,
        "formset": formset,
        "occupied_ids": sorted(list(occupied_map.keys())),
        "occupied_map": occupied_map,
        "hours": 12,
        "datalist_choferes": list(
            SalidaProgramada.objects.exclude(chofer="")
            .values_list("chofer", flat=True)
            .distinct()
            .order_by("chofer")[:300]
        ),
    }
    return render(request, "flota/diagrama_reemplazos.html", ctx)
