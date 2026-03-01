from __future__ import annotations

from django import forms
from django.forms import inlineformset_factory

from inventario.models import Producto
from .models import ProductoImagen


class ProductoImagenForm(forms.ModelForm):
    """
    Evita que formularios extra vacíos queden "changed" por defaults (ej: orden=1)
    y rompan el guardado de la imagen real.
    """

    class Meta:
        model = ProductoImagen
        fields = ("imagen", "titulo", "orden")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "titulo" in self.fields:
            self.fields["titulo"].required = False

        if "orden" in self.fields:
            self.fields["orden"].required = False
            # En forms extra (sin pk), no uses initial por default del modelo
            if not getattr(self.instance, "pk", None):
                self.initial.pop("orden", None)
                self.fields["orden"].initial = None

    def has_changed(self) -> bool:
        changed = super().has_changed()
        if not changed:
            return False

        imagen_key = self.add_prefix("imagen")
        titulo_key = self.add_prefix("titulo")
        orden_key = self.add_prefix("orden")
        delete_key = self.add_prefix("DELETE")

        if (self.data.get(delete_key) or "").strip():
            return True

        has_file = bool(self.files.get(imagen_key))
        titulo = (self.data.get(titulo_key) or "").strip()
        orden = (self.data.get(orden_key) or "").strip()

        # Si no hay archivo ni título y el orden es vacío/1, tratarlo como vacío
        if (not has_file) and (not titulo) and (orden in ("", "1")):
            return False

        return True


ProductoImagenFormSet = inlineformset_factory(
    parent_model=Producto,
    model=ProductoImagen,
    form=ProductoImagenForm,
    extra=2,
    can_delete=True,
)

# Backwards-compat: nombre viejo usado por inventario/views.py
ProductoImagenInlineFormSet = ProductoImagenFormSet

