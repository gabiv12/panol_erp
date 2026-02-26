from __future__ import annotations

from django import forms

from .choferes_models import Chofer


class ChoferForm(forms.ModelForm):
    class Meta:
        model = Chofer
        fields = [
            "apellido",
            "nombre",
            "legajo",
            "telefono",
            "is_active",
            "observaciones",
            "foto_1",
            "foto_2",
        ]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            "apellido": "Ej: PÉREZ",
            "nombre": "Ej: Nombre",
            "legajo": "Opcional (si existe)",
            "telefono": "Opcional",
            "observaciones": "Opcional. Ej: licencia, notas internas.",
        }
        for k, v in placeholders.items():
            if k in self.fields:
                self.fields[k].widget.attrs.setdefault("placeholder", v)

        help_texts = {"foto_1": "Opcional. Máximo 20 MB.", "foto_2": "Opcional. Máximo 20 MB."}
        for k, v in help_texts.items():
            if k in self.fields:
                self.fields[k].help_text = v

        for _, field in self.fields.items():
            w = field.widget
            cls = (w.attrs.get("class") or "").strip()
            if isinstance(w, forms.CheckboxInput):
                continue
            if "ti-input" not in cls:
                w.attrs["class"] = (cls + " ti-input").strip()
