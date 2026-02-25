from __future__ import annotations

import django_filters
from django import forms
from django.db.models import Q
from django.utils import timezone

from flota.models import Colectivo

from .models import Categoria, MovimientoStock, Producto, Proveedor, StockActual, Subcategoria, Ubicacion


_BOOL_CHOICES = (
    ("", "---------"),
    ("true", "Sí"),
    ("false", "No"),
)


class ProductoFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="filter_q",
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "ti-input",
                "placeholder": "Código, nombre o descripción…",
                "autocomplete": "off",
            }
        ),
    )

    categoria = django_filters.ModelChoiceFilter(
        queryset=Categoria.objects.all().order_by("nombre"),
        label="Categoría",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    subcategoria = django_filters.ModelChoiceFilter(
        queryset=Subcategoria.objects.all().order_by("nombre"),
        label="Subcategoría",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    proveedor = django_filters.ModelChoiceFilter(
        queryset=Proveedor.objects.all().order_by("nombre"),
        label="Proveedor",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    is_active = django_filters.BooleanFilter(
        field_name="is_active",
        label="Activo",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}, choices=_BOOL_CHOICES),
    )

    class Meta:
        model = Producto
        fields = ["q", "categoria", "subcategoria", "proveedor", "is_active"]

    def filter_q(self, qs, name, value):
        if not value:
            return qs
        v = value.strip()
        return qs.filter(Q(codigo__icontains=v) | Q(nombre__icontains=v) | Q(descripcion__icontains=v))


class UbicacionFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="filter_q",
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "ti-input",
                "placeholder": "Código, nombre o referencia…",
                "autocomplete": "off",
            }
        ),
    )

    is_active = django_filters.BooleanFilter(
        field_name="is_active",
        label="Activa",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}, choices=_BOOL_CHOICES),
    )

    class Meta:
        model = Ubicacion
        fields = ["q", "is_active"]

    def filter_q(self, qs, name, value):
        if not value:
            return qs
        v = value.strip()
        return qs.filter(
            Q(codigo__icontains=v)
            | Q(nombre__icontains=v)
            | Q(referencia__icontains=v)
            | Q(descripcion__icontains=v)
        )


class MovimientoStockFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="filter_q",
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "ti-input",
                "placeholder": "Producto, ubicación, referencia, unidad…",
                "autocomplete": "off",
            }
        ),
    )

    producto = django_filters.ModelChoiceFilter(
        queryset=Producto.objects.all().order_by("nombre"),
        label="Producto",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    ubicacion = django_filters.ModelChoiceFilter(
        queryset=Ubicacion.objects.all().order_by("codigo"),
        label="Ubicación",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    tipo = django_filters.ChoiceFilter(
        choices=MovimientoStock.Tipo.choices,
        label="Tipo",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    colectivo = django_filters.ModelChoiceFilter(
        queryset=Colectivo.objects.filter(is_active=True).order_by("interno"),
        label="Unidad",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    proveedor = django_filters.ModelChoiceFilter(
        queryset=Proveedor.objects.all().order_by("nombre"),
        label="Proveedor",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    usuario = django_filters.CharFilter(
        field_name="usuario__username",
        lookup_expr="icontains",
        label="Usuario",
        required=False,
        widget=forms.TextInput(attrs={"class": "ti-input", "placeholder": "username…"}),
    )

    # Filtro virtual (NO va en Meta.fields): últimos N días
    days = django_filters.NumberFilter(
        method="filter_days",
        label="Días",
        required=False,
        widget=forms.NumberInput(attrs={"class": "ti-input", "min": "1", "max": "365"}),
    )

    class Meta:
        model = MovimientoStock
        fields = ["q", "producto", "ubicacion", "tipo", "colectivo", "proveedor", "usuario"]

    def filter_days(self, qs, name, value):
        if value in (None, ""):
            return qs
        try:
            days = int(value)
        except Exception:
            return qs
        if days <= 0:
            return qs
        since = timezone.now() - timezone.timedelta(days=days)
        return qs.filter(fecha__gte=since)

    def filter_q(self, qs, name, value):
        if not value:
            return qs

        v = value.strip()

        q = (
            Q(producto__codigo__icontains=v)
            | Q(producto__nombre__icontains=v)
            | Q(ubicacion__codigo__icontains=v)
            | Q(ubicacion__nombre__icontains=v)
            | Q(referencia__icontains=v)
            | Q(observaciones__icontains=v)
            | Q(colectivo__dominio__icontains=v)
        )

        if v.isdigit():
            q |= Q(colectivo__interno=int(v))

        return qs.filter(q)


class StockActualFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="filter_q",
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "ti-input",
                "placeholder": "Producto o ubicación…",
                "autocomplete": "off",
            }
        ),
    )

    ubicacion = django_filters.ModelChoiceFilter(
        queryset=Ubicacion.objects.all().order_by("codigo"),
        label="Ubicación",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    producto = django_filters.ModelChoiceFilter(
        queryset=Producto.objects.all().order_by("nombre"),
        label="Producto",
        required=False,
        widget=forms.Select(attrs={"class": "ti-input"}),
    )

    class Meta:
        model = StockActual
        fields = ["q", "ubicacion", "producto"]

    def filter_q(self, qs, name, value):
        if not value:
            return qs
        v = value.strip()
        return qs.filter(
            Q(producto__codigo__icontains=v)
            | Q(producto__nombre__icontains=v)
            | Q(ubicacion__codigo__icontains=v)
            | Q(ubicacion__nombre__icontains=v)
        )
