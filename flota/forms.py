from django import forms
from .models import Colectivo


class ColectivoForm(forms.ModelForm):
    class Meta:
        model = Colectivo
        fields = [
            "interno",
            "dominio",
            "anio_modelo",
            "marca",
            "modelo",
            "numero_chasis",
            "carroceria_marca",

            "revision_tecnica_vto",
            "matafuego_vto",
            "matafuego_ult_control",

            "odometro_km",
            "odometro_fecha",

            "aceite_intervalo_km",
            "aceite_ultimo_cambio_km",
            "aceite_ultimo_cambio_fecha",
            "aceite_obs",

            "filtros_intervalo_km",
            "filtros_ultimo_cambio_km",
            "filtros_ultimo_cambio_fecha",
            "filtros_obs",

            "limpieza_ultima_fecha",
            "limpieza_realizada_por",
            "limpieza_obs",

            "tiene_gps",
            "usa_biodiesel",
            "tipo_servicio",
            "jurisdiccion",
            "estado",
            "observaciones",
            "is_active",
        ]
        widgets = {
            "revision_tecnica_vto": forms.DateInput(attrs={"type": "date"}),
            "matafuego_vto": forms.DateInput(attrs={"type": "date"}),
            "matafuego_ult_control": forms.DateInput(attrs={"type": "date"}),

            "odometro_fecha": forms.DateInput(attrs={"type": "date"}),
            "aceite_ultimo_cambio_fecha": forms.DateInput(attrs={"type": "date"}),
            "filtros_ultimo_cambio_fecha": forms.DateInput(attrs={"type": "date"}),
            "limpieza_ultima_fecha": forms.DateInput(attrs={"type": "date"}),

            "observaciones": forms.Textarea(),
            "aceite_obs": forms.Textarea(),
            "filtros_obs": forms.Textarea(),
            "limpieza_obs": forms.Textarea(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            w = field.widget

            if isinstance(w, forms.CheckboxInput):
                base_class = "ti-checkbox"
            elif isinstance(w, forms.Textarea):
                base_class = "ti-textarea"
            elif isinstance(w, forms.Select):
                base_class = "ti-select"
            else:
                base_class = "ti-input"

            current = w.attrs.get("class", "")
            w.attrs["class"] = (current + " " + base_class).strip()

            if not w.attrs.get("placeholder") and name in ("dominio", "marca", "modelo", "jurisdiccion", "limpieza_realizada_por"):
                w.attrs["placeholder"] = field.label