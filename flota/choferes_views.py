from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .choferes_forms import ChoferForm
from .choferes_models import Chofer


@login_required
@permission_required("flota.view_chofer", raise_exception=True)
def chofer_list(request):
    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "activos").strip()

    qs = Chofer.objects.all()

    if estado == "activos":
        qs = qs.filter(is_active=True)
    elif estado == "inactivos":
        qs = qs.filter(is_active=False)

    if q:
        qs = qs.filter(Q(apellido__icontains=q) | Q(nombre__icontains=q) | Q(legajo__icontains=q))

    qs = qs.order_by("apellido", "nombre", "id")[:500]

    return render(request, "flota/chofer_list.html", {"items": qs, "q": q, "estado": estado})


@login_required
@permission_required("flota.add_chofer", raise_exception=True)
def chofer_create(request):
    if request.method == "POST":
        form = ChoferForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Chofer creado: {obj.display_name}.")
            return redirect(reverse_lazy("flota:chofer_list"))
        messages.error(request, "No se pudo guardar. Revisá los campos marcados.")
    else:
        form = ChoferForm()

    return render(request, "flota/chofer_form.html", {"form": form, "mode": "create"})


@login_required
@permission_required("flota.change_chofer", raise_exception=True)
def chofer_update(request, pk: int):
    obj = get_object_or_404(Chofer, pk=pk)

    if request.method == "POST":
        form = ChoferForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Chofer actualizado: {obj.display_name}.")
            return redirect(reverse_lazy("flota:chofer_list"))
        messages.error(request, "No se pudo guardar. Revisá los campos marcados.")
    else:
        form = ChoferForm(instance=obj)

    return render(request, "flota/chofer_form.html", {"form": form, "mode": "update", "obj": obj})


@login_required
@permission_required("flota.change_chofer", raise_exception=True)
def chofer_toggle_activo(request, pk: int):
    obj = get_object_or_404(Chofer, pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=["is_active"])

    messages.success(request, f"Chofer {'activado' if obj.is_active else 'desactivado'}: {obj.display_name}.")
    return redirect(reverse_lazy("flota:chofer_list"))
