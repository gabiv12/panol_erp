from __future__ import annotations

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from inventario.models import Producto
from .models import ProductoImagen


MAX_IMG_MB = 4
MAX_IMG_BYTES = MAX_IMG_MB * 1024 * 1024


class ProductoImagenForm(forms.ModelForm):
    class Meta:
        model = ProductoImagen
        fields = ["imagen", "titulo", "orden"]

        widgets = {
            "imagen": forms.ClearableFileInput(attrs={"class": "ti-input", "accept": "image/*"}),
            "titulo": forms.TextInput(attrs={"class": "ti-input", "placeholder": "Opcional (ej: frente / etiqueta / detalle)"}),
            "orden": forms.NumberInput(attrs={"class": "ti-input", "min": 1}),
        }

    def clean_imagen(self):
        f = self.cleaned_data.get("imagen")
        if not f:
            return f

        if hasattr(f, "size") and f.size > MAX_IMG_BYTES:
            raise ValidationError(f"Imagen demasiado grande. Máximo {MAX_IMG_MB} MB.")

        return f


ProductoImagenInlineFormSet = inlineformset_factory(
    Producto,
    ProductoImagen,
    form=ProductoImagenForm,
    extra=2,
    max_num=2,
    can_delete=True,
    validate_max=True,
)