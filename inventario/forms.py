
from __future__ import annotations

from decimal import Decimal
from flota.models import Colectivo
from django import forms
from django.core.exceptions import ValidationError



from .models import (
    Categoria,
    Subcategoria,
    UnidadMedida,
    Ubicacion,
    Proveedor,
    Producto,
    MovimientoStock,
)


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "is_active"]


class SubcategoriaForm(forms.ModelForm):
    class Meta:
        model = Subcategoria
        fields = ["categoria", "nombre", "descripcion", "is_active"]


class UnidadMedidaForm(forms.ModelForm):
    class Meta:
        model = UnidadMedida
        fields = ["nombre", "abreviatura", "permite_decimales", "is_active"]


class UbicacionForm(forms.ModelForm):
    """Ubicación física."""

    class Meta:
        model = Ubicacion
        fields = [
            "codigo",
            "nombre",
            "tipo",
            "padre",
            "pasillo",
            "modulo",
            "nivel",
            "posicion",
            "permite_transferencias",
            "referencia",
            "descripcion",
            "is_active",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "codigo": "Código único (lo que pegás en la ubicación). Ej: DP-A01-M01-N01-P01",
            "padre": "Opcional. Usalo para armar árbol (Depósito → Estante → Posición).",
            "pasillo": "Opcional. Ej: A, B, C.",
            "modulo": "Opcional. Ej: 01, 02.",
            "nivel": "Opcional. Ej: 01, 02.",
            "posicion": "Opcional. Ej: 01, 02.",
            "permite_transferencias": "Si está activo, se permite transferir stock hacia/desde esta ubicación.",
        }

    def clean(self):
        cleaned = super().clean()

        codigo = cleaned.get("codigo")
        if codigo:
            cleaned["codigo"] = str(codigo).strip().upper()

        pasillo = cleaned.get("pasillo")
        if pasillo:
            cleaned["pasillo"] = str(pasillo).strip().upper()

        if any(cleaned.get(k) for k in ("pasillo", "modulo", "nivel", "posicion")):
            if not cleaned.get("nombre"):
                raise ValidationError("Si cargás pasillo/módulo/nivel/posición, completá también el nombre.")

        return cleaned


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "cuit", "telefono", "email", "direccion", "is_active"]


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "categoria",
            "subcategoria",
            "unidad_medida",
            "proveedor",
            "stock_minimo",
            "maneja_vencimiento",
            "is_active",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }


class MovimientoStockForm(forms.ModelForm):
    """Movimiento de stock.

    IMPORTANTE: 'fecha' es auto_now_add (no editable) → no debe estar en Meta.fields.
    """

    class Meta:
        model = MovimientoStock
        fields = [
            "producto",
            "ubicacion",
            "ubicacion_destino",
            "tipo",
            "colectivo",
            "cantidad",
            "proveedor",
            "referencia",
            "lote",
            "fecha_vencimiento",
            "observaciones",
        ]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 3}),
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        # UX: defaults
        self.fields["cantidad"].widget.attrs.setdefault("step", "0.001")

        # Unidades (opcional)
        if "colectivo" in self.fields:
            self.fields["colectivo"].queryset = Colectivo.objects.filter(is_active=True).order_by("interno")
            self.fields["colectivo"].required = False
            self.fields["colectivo"].empty_label = "Sin unidad (no vincular)"
            self.fields["colectivo"].widget.attrs.setdefault("class", "ti-input")

        # Solo mostrar ubicaciones habilitadas para transferencias
        if "ubicacion" in self.fields:
            self.fields["ubicacion"].queryset = Ubicacion.objects.filter(is_active=True)
        if "ubicacion_destino" in self.fields:
            self.fields["ubicacion_destino"].queryset = Ubicacion.objects.filter(is_active=True, permite_transferencias=True)

        if self.instance and self.instance.pk:
            self.fields["tipo"].disabled = False

        self._toggle_fields_by_tipo(initial=True)

    def clean(self):
        cleaned = super().clean()

        tipo = cleaned.get("tipo")
        qty = cleaned.get("cantidad")
        ubic = cleaned.get("ubicacion")
        dest = cleaned.get("ubicacion_destino")

        if qty is not None:
            try:
                qty = Decimal(qty)
            except Exception:
                raise ValidationError({"cantidad": "Cantidad inválida."})

        if tipo == MovimientoStock.Tipo.TRANSFERENCIA:
            if not dest:
                raise ValidationError({"ubicacion_destino": "Seleccioná una ubicación destino."})
            if ubic and dest and ubic.pk == dest.pk:
                raise ValidationError({"ubicacion_destino": "Destino debe ser distinto al origen."})

        if qty is not None and tipo:
            if tipo in (MovimientoStock.Tipo.INGRESO, MovimientoStock.Tipo.EGRESO, MovimientoStock.Tipo.TRANSFERENCIA):
                if qty <= 0:
                    raise ValidationError({"cantidad": "La cantidad debe ser mayor a 0."})
            elif tipo == MovimientoStock.Tipo.AJUSTE:
                if qty == 0:
                    raise ValidationError({"cantidad": "El ajuste no puede ser 0."})

        return cleaned

    def _toggle_fields_by_tipo(self, initial: bool = False):
        tipo = self.initial.get("tipo") if initial else self.data.get("tipo") or self.cleaned_data.get("tipo")
        is_transfer = (tipo == MovimientoStock.Tipo.TRANSFERENCIA)

        if "ubicacion_destino" in self.fields:
            self.fields["ubicacion_destino"].required = is_transfer