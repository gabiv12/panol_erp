from __future__ import annotations

from django import forms

from .models import ParteDiario, ParteDiarioAdjunto


class ParteDiarioForm(forms.ModelForm):
    class Meta:
        model = ParteDiario
        fields = [
            "colectivo",
            "fecha_evento",
            "tipo",
            "severidad",
            "estado",
            "odometro_km",
            "accion_mantenimiento",
            "km_mantenimiento",
            "matafuego_vto_nuevo",
            "auxilio_inicio",
            "auxilio_fin",
            "descripcion",
            "observaciones",
        ]
        widgets = {
            "fecha_evento": forms.DateTimeInput(attrs={"class": "ti-input", "type": "datetime-local"}),
            "tipo": forms.Select(attrs={"class": "ti-input"}),
            "severidad": forms.Select(attrs={"class": "ti-input"}),
            "estado": forms.Select(attrs={"class": "ti-input"}),
            "colectivo": forms.Select(attrs={"class": "ti-input"}),
            "odometro_km": forms.NumberInput(attrs={"class": "ti-input", "placeholder": "Ej: 152340"}),
            "accion_mantenimiento": forms.Select(attrs={"class": "ti-input"}),
            "km_mantenimiento": forms.NumberInput(attrs={"class": "ti-input", "placeholder": "Ej: 152340"}),
            "matafuego_vto_nuevo": forms.DateInput(attrs={"class": "ti-input", "type": "date"}),
            "auxilio_inicio": forms.DateTimeInput(attrs={"class": "ti-input", "type": "datetime-local"}),
            "auxilio_fin": forms.DateTimeInput(attrs={"class": "ti-input", "type": "datetime-local"}),
            "descripcion": forms.Textarea(attrs={"class": "ti-input", "rows": 4}),
            "observaciones": forms.Textarea(attrs={"class": "ti-input", "rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        accion = (cleaned.get("accion_mantenimiento") or "").strip()
        km_mant = cleaned.get("km_mantenimiento")

        if tipo == ParteDiario.Tipo.MANTENIMIENTO:
            if not accion:
                self.add_error("accion_mantenimiento", "Seleccioná una acción de mantenimiento.")
            if accion in (ParteDiario.AccionMantenimiento.ACEITE, ParteDiario.AccionMantenimiento.FILTROS) and not km_mant:
                self.add_error("km_mantenimiento", "Para aceite/filtros conviene cargar el km.")
        else:
            # Si no es mantenimiento, limpiamos para que no quede basura
            cleaned["accion_mantenimiento"] = ""
            cleaned["km_mantenimiento"] = None
            cleaned["matafuego_vto_nuevo"] = None

        if tipo == ParteDiario.Tipo.AUXILIO:
            ini = cleaned.get("auxilio_inicio")
            fin = cleaned.get("auxilio_fin")
            if (ini and not fin) or (fin and not ini):
                self.add_error("auxilio_fin", "Si cargás auxilio, completá inicio y fin.")
            if ini and fin and fin < ini:
                self.add_error("auxilio_fin", "Fin de auxilio no puede ser menor que inicio.")

        return cleaned


class ParteDiarioAdjuntoForm(forms.ModelForm):
    class Meta:
        model = ParteDiarioAdjunto
        fields = ["archivo", "descripcion"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "ti-input", "placeholder": "Ej: Foto del problema / Boleta / Evidencia"}),
        }