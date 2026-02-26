from __future__ import annotations

from django import forms

from .models import ParteDiario, ParteDiarioAdjunto


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


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

            "chofer_label",
            "parte_mecanico",
            "parte_electrico",
            "trabajos_carroceria_varios",
            "combustible_ruta_detalle",

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

            "chofer_label": forms.TextInput(attrs={"class": "ti-input", "list": "dl_choferes", "placeholder": "Ej: APELLIDO, Nombre"}),
            "parte_mecanico": forms.Textarea(attrs={"class": "ti-input", "rows": 4}),
            "parte_electrico": forms.Textarea(attrs={"class": "ti-input", "rows": 4}),
            "trabajos_carroceria_varios": forms.Textarea(attrs={"class": "ti-input", "rows": 4}),
            "combustible_ruta_detalle": forms.Textarea(attrs={"class": "ti-input", "rows": 3}),

            "accion_mantenimiento": forms.Select(attrs={"class": "ti-input"}),
            "km_mantenimiento": forms.NumberInput(attrs={"class": "ti-input", "placeholder": "Ej: 152340"}),
            "matafuego_vto_nuevo": forms.DateInput(attrs={"class": "ti-input", "type": "date"}),
            "auxilio_inicio": forms.DateTimeInput(attrs={"class": "ti-input", "type": "datetime-local"}),
            "auxilio_fin": forms.DateTimeInput(attrs={"class": "ti-input", "type": "datetime-local"}),

            "descripcion": forms.HiddenInput(),
            "observaciones": forms.Textarea(attrs={"class": "ti-input", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Backward compatible: tests/flows viejos mandan "descripcion".
        if "descripcion" in self.fields:
            self.fields["descripcion"].required = False

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        accion = (cleaned.get("accion_mantenimiento") or "").strip()
        km_mant = cleaned.get("km_mantenimiento")

        # Texto nuevo (planilla)
        m = (cleaned.get("parte_mecanico") or "").strip()
        e = (cleaned.get("parte_electrico") or "").strip()
        c = (cleaned.get("trabajos_carroceria_varios") or "").strip()
        comb = (cleaned.get("combustible_ruta_detalle") or "").strip()
        obs = (cleaned.get("observaciones") or "").strip()

        # Texto legacy
        desc_legacy = (cleaned.get("descripcion") or "").strip()

        # Requerir contenido: acepta legacy o el nuevo esquema
        if not (m or e or c or comb or obs or desc_legacy):
            self.add_error(
                "parte_mecanico",
                "Cargá al menos una descripción (mecánico / eléctrico / carrocería / combustible / observaciones).",
            )

        if tipo == ParteDiario.Tipo.MANTENIMIENTO:
            if not accion:
                self.add_error("accion_mantenimiento", "Seleccioná una acción de mantenimiento.")
            if accion in (ParteDiario.AccionMantenimiento.ACEITE, ParteDiario.AccionMantenimiento.FILTROS) and not km_mant:
                self.add_error("km_mantenimiento", "Para aceite/filtros conviene cargar el km.")
        else:
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
        else:
            cleaned["auxilio_inicio"] = None
            cleaned["auxilio_fin"] = None

        return cleaned

    def save(self, commit=True):
        obj: ParteDiario = super().save(commit=False)

        parts = []
        if (obj.parte_mecanico or "").strip():
            parts.append("MECÁNICO: " + (obj.parte_mecanico or "").strip())
        if (obj.parte_electrico or "").strip():
            parts.append("ELÉCTRICO: " + (obj.parte_electrico or "").strip())
        if (obj.trabajos_carroceria_varios or "").strip():
            parts.append("CARROCERÍA/VARIOS: " + (obj.trabajos_carroceria_varios or "").strip())
        if (obj.combustible_ruta_detalle or "").strip():
            parts.append("COMBUSTIBLE EN RUTA: " + (obj.combustible_ruta_detalle or "").strip())
        if (obj.observaciones or "").strip():
            parts.append("OBSERVACIONES: " + (obj.observaciones or "").strip())

        # Si hay texto nuevo, autogenerar. Si no, respetar "descripcion" legacy.
        if parts:
            obj.descripcion = "\n\n".join(parts)
        else:
            if not (obj.descripcion or "").strip():
                obj.descripcion = "(sin descripción)"

        if commit:
            obj.save()
            self.save_m2m()

        return obj


class ParteDiarioAdjuntoForm(forms.ModelForm):
    class Meta:
        model = ParteDiarioAdjunto
        fields = ["archivo", "descripcion"]
        widgets = {
            "archivo": forms.ClearableFileInput(attrs={"class": "ti-input"}),
            "descripcion": forms.TextInput(attrs={"class": "ti-input", "placeholder": "Ej: Foto del problema / Boleta / Evidencia"}),
        }


class ParteDiarioChoferForm(forms.ModelForm):
    fotos = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"class": "ti-input", "multiple": True}),
        help_text="Opcional. Podés seleccionar varias fotos.",
    )

    class Meta:
        model = ParteDiario
        fields = [
            "colectivo",
            "odometro_km",
            "chofer_label",
            "parte_mecanico",
            "parte_electrico",
            "trabajos_carroceria_varios",
            "combustible_ruta_detalle",
        ]
        widgets = {
            "colectivo": forms.Select(attrs={"class": "ti-input"}),
            "odometro_km": forms.NumberInput(attrs={"class": "ti-input", "placeholder": "Ej: 152340"}),
            "chofer_label": forms.TextInput(attrs={"class": "ti-input", "list": "dl_choferes", "placeholder": "Ej: APELLIDO, Nombre"}),
            "parte_mecanico": forms.Textarea(attrs={"class": "ti-input", "rows": 4}),
            "parte_electrico": forms.Textarea(attrs={"class": "ti-input", "rows": 4}),
            "trabajos_carroceria_varios": forms.Textarea(attrs={"class": "ti-input", "rows": 4}),
            "combustible_ruta_detalle": forms.Textarea(attrs={"class": "ti-input", "rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        m = (cleaned.get("parte_mecanico") or "").strip()
        e = (cleaned.get("parte_electrico") or "").strip()
        c = (cleaned.get("trabajos_carroceria_varios") or "").strip()

        if not (m or e or c):
            self.add_error("parte_mecanico", "Cargá al menos un texto (mecánico / eléctrico / carrocería).")

        return cleaned
