from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import ROLE_CHOICES, user_role, MODULE_CHOICES, user_modules
from .forms import UsuarioCreateForm, UsuarioUpdateForm


def _is_superadmin(u):
    return bool(u and u.is_authenticated and u.is_superuser)


@login_required
@user_passes_test(_is_superadmin)
def usuario_list(request):
    q = request.GET.get("q", "").strip()

    qs = User.objects.all().order_by("username").prefetch_related("groups")
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )

    role_label = dict(ROLE_CHOICES)
    mod_label = dict(MODULE_CHOICES)

    for u in qs:
        rk = user_role(u)
        u.role_key = rk
        u.role_label = role_label.get(rk, "—")
        u.modules_labels = [mod_label.get(k, k) for k in user_modules(u)]

    return render(
        request,
        "usuarios/usuario_list.html",
        {
            "usuarios": qs,
            "q": q,
        },
    )


@login_required
@user_passes_test(_is_superadmin)
def usuario_create(request):
    if request.method == "POST":
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("usuarios:usuario_list")
    else:
        form = UsuarioCreateForm()

    return render(
        request,
        "usuarios/usuario_form.html",
        {
            "form": form,
            "modo": "crear",
            "obj": None,
        },
    )


@login_required
@user_passes_test(_is_superadmin)
def usuario_update(request, pk):
    obj = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UsuarioUpdateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("usuarios:usuario_list")
    else:
        form = UsuarioUpdateForm(instance=obj)

    return render(
        request,
        "usuarios/usuario_form.html",
        {
            "form": form,
            "modo": "editar",
            "obj": obj,
        },
    )


@login_required
@user_passes_test(_is_superadmin)
def usuario_delete(request, pk):
    obj = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        obj.delete()
        messages.success(request, "Usuario eliminado correctamente.")
        return redirect("usuarios:usuario_list")

    return render(
        request,
        "usuarios/usuario_confirm_delete.html",
        {
            "obj": obj,
        },
    )
