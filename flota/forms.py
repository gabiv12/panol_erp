from __future__ import annotations

from django import forms

from .models import Colectivo, SalidaProgramada


class ColectivoForm(forms.ModelForm):
    """
    Formulario de Colectivo (Unidad).

    Nota:
    - Se corrigen labels/help_text con mojibake acá (y no en el modelo),
      para evitar migraciones de "verbose_name" que no aportan al negocio.
    """

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
            "matafuego_1_vto",
            "matafuego_2_vto",
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
            "matafuego_1_vto": forms.DateInput(attrs={"type": "date"}),
            "matafuego_2_vto": forms.DateInput(attrs={"type": "date"}),
            "matafuego_ult_control": forms.DateInput(attrs={"type": "date"}),
            "odometro_fecha": forms.DateInput(attrs={"type": "date"}),
            "aceite_ultimo_cambio_fecha": forms.DateInput(attrs={"type": "date"}),
            "filtros_ultimo_cambio_fecha": forms.DateInput(attrs={"type": "date"}),
            "limpieza_ultima_fecha": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 4}),
            "aceite_obs": forms.Textarea(attrs={"rows": 3}),
            "filtros_obs": forms.Textarea(attrs={"rows": 3}),
            "limpieza_obs": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        labels = {
            "anio_modelo": "Año modelo",
            "numero_chasis": "Número de chasis",
            "carroceria_marca": "Carrocería (marca)",
            "revision_tecnica_vto": "Vencimiento revisión técnica",
            "matafuego_ult_control": "Último control de matafuego",
            "odometro_km": "Odómetro (km)",
            "odometro_fecha": "Fecha odómetro",
            "aceite_ultimo_cambio_km": "Último cambio aceite (km)",
            "aceite_ultimo_cambio_fecha": "Fecha último cambio aceite",
            "filtros_ultimo_cambio_km": "Último cambio filtros (km)",
            "filtros_ultimo_cambio_fecha": "Fecha último cambio filtros",
            "limpieza_ultima_fecha": "Última limpieza",
            "jurisdiccion": "Jurisdicción",
        }

        help_texts = {
            "interno": "Número interno de la unidad (identificador operativo).",
            "dominio": "Dominio/patente. Se recomienda cargar en mayúsculas.",
            "numero_chasis": "Número/VIN del chasis. Puede cargarse después; si está vacío no se valida unicidad.",
            "matafuego_ult_control": "Fecha del último control/recarga del matafuego.",
            "odometro_fecha": "Fecha en la que se registró el odómetro.",
            "aceite_intervalo_km": "Cada cuántos km corresponde cambio de aceite (ej: 10000).",
            "aceite_ultimo_cambio_km": "KM del último cambio de aceite.",
            "aceite_obs": "Motivo si se cambió antes de tiempo, observaciones, etc.",
            "filtros_intervalo_km": "Cada cuántos km corresponde cambio de filtros (ej: 20000).",
            "filtros_ultimo_cambio_km": "KM del último cambio de filtros.",
            "filtros_obs": "Motivo si se cambió antes de tiempo, observaciones, etc.",
            "limpieza_ultima_fecha": "Fecha de la última limpieza registrada.",
        }

        for k, v in labels.items():
            if k in self.fields:
                self.fields[k].label = v

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

        inst = getattr(self, "instance", None)
        if inst and getattr(inst, "pk", None):
            if not inst.matafuego_1_vto and getattr(inst, "matafuego_vto", None):
                self.initial.setdefault("matafuego_1_vto", inst.matafuego_vto)
            legacy2 = getattr(inst, "matafuego_vencimiento_2", None)
            if not inst.matafuego_2_vto and legacy2:
                self.initial.setdefault("matafuego_2_vto", legacy2)

    def save(self, commit=True):
        obj: Colectivo = super().save(commit=False)

        v1 = obj.matafuego_1_vto or getattr(obj, "matafuego_vto", None)
        v2 = obj.matafuego_2_vto or getattr(obj, "matafuego_vencimiento_2", None)

        fechas = [d for d in (v1, v2) if d]
        obj.matafuego_vto = min(fechas) if fechas else None

        if hasattr(obj, "matafuego_vencimiento_2"):
            obj.matafuego_vencimiento_2 = obj.matafuego_2_vto

        if commit:
            obj.save()
            self.save_m2m()

        return obj


class SalidaProgramadaForm(forms.ModelForm):
    """
    Formulario de carga de salidas.

    Se agregan datalists (autocompletado) para acelerar la carga del diagrama.
    """

    class Meta:
        model = SalidaProgramada
        fields = [
            "colectivo",
            "salida_programada",
            "llegada_programada",
            "tipo",
            "estado",
            "seccion",
            "salida_label",
            "chofer",
            "regreso",
            "recorrido",
            "nota",
        ]
        widgets = {
            "salida_programada": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "llegada_programada": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Placeholders operativos
        if "seccion" in self.fields:
            self.fields["seccion"].widget.attrs.setdefault("placeholder", "Ej: SÁENZ PEÑA - RESISTENCIA")
            self.fields["seccion"].widget.attrs.setdefault("list", "dl_secciones")
        if "salida_label" in self.fields:
            self.fields["salida_label"].widget.attrs.setdefault("placeholder", "Ej: 05:00 DIRECTO / RCIA 06:00HS DIRECTO")
            self.fields["salida_label"].widget.attrs.setdefault("list", "dl_etiquetas")
        if "regreso" in self.fields:
            self.fields["regreso"].widget.attrs.setdefault("placeholder", "Ej: 12:00 DIR / 09:00 INT / **")
            self.fields["regreso"].widget.attrs.setdefault("list", "dl_regresos")
        if "recorrido" in self.fields:
            self.fields["recorrido"].widget.attrs.setdefault("placeholder", "Ej: S PEÑA - CASTELLI / MIRAF - S PEÑA")
            self.fields["recorrido"].widget.attrs.setdefault("list", "dl_recorridos")
        if "chofer" in self.fields:
            self.fields["chofer"].widget.attrs.setdefault("placeholder", "Nombre y apellido")
            self.fields["chofer"].widget.attrs.setdefault("list", "dl_choferes")
        if "nota" in self.fields:
            self.fields["nota"].widget.attrs.setdefault("placeholder", "Observación corta")

        for _, field in self.fields.items():
            w = field.widget
            cls = (w.attrs.get("class") or "").strip()
            if isinstance(w, forms.CheckboxInput):
                continue
            if "ti-input" not in cls:
                w.attrs["class"] = (cls + " ti-input").strip()


class SalidaProgramadaBulkForm(forms.ModelForm):
    """Formulario compacto para editar el diagrama del dÃ­a en tabla (reemplazos rÃ¡pidos).

    En operaciÃ³n real, la mayorÃ­a de horarios/etiquetas/recorridos son fijos.
    En esta pantalla se permite cambiar SOLO:
      - Unidad (colectivo)
      - Chofer

    Para cambios de horario o ediciÃ³n completa (ej: viajes ESPECIALES), usÃ¡:
      Horarios -> Editar (o "Editar completo" desde esta tabla).
    """

    class Meta:
        model = SalidaProgramada
        fields = [
            "colectivo",
            "chofer",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "chofer" in self.fields:
            self.fields["chofer"].widget.attrs.setdefault("placeholder", "Nombre y apellido")
            self.fields["chofer"].widget.attrs.setdefault("list", "dl_choferes")

        for _, field in self.fields.items():
            w = field.widget
            cls = (w.attrs.get("class") or "").strip()
            if isinstance(w, forms.CheckboxInput):
                continue
            if "ti-input" not in cls:
                w.attrs["class"] = (cls + " ti-input").strip()

