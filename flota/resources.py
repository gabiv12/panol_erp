from import_export import resources, fields
from import_export.widgets import BooleanWidget, DateWidget

from .models import Colectivo


class ColectivoResource(resources.ModelResource):
    interno = fields.Field(attribute="interno", column_name="interno")

    tiene_gps = fields.Field(
        attribute="tiene_gps",
        column_name="tiene_gps",
        widget=BooleanWidget(),
    )
    usa_biodiesel = fields.Field(
        attribute="usa_biodiesel",
        column_name="usa_biodiesel",
        widget=BooleanWidget(),
    )

    revision_tecnica_vto = fields.Field(
        attribute="revision_tecnica_vto",
        column_name="revision_tecnica_vto",
        widget=DateWidget(format="%Y-%m-%d"),
    )
    matafuego_vto = fields.Field(
        attribute="matafuego_vto",
        column_name="matafuego_vto",
        widget=DateWidget(format="%Y-%m-%d"),
    )
    matafuego_ult_control = fields.Field(
        attribute="matafuego_ult_control",
        column_name="matafuego_ult_control",
        widget=DateWidget(format="%Y-%m-%d"),
    )

    odometro_fecha = fields.Field(
        attribute="odometro_fecha",
        column_name="odometro_fecha",
        widget=DateWidget(format="%Y-%m-%d"),
    )
    aceite_ultimo_cambio_fecha = fields.Field(
        attribute="aceite_ultimo_cambio_fecha",
        column_name="aceite_ultimo_cambio_fecha",
        widget=DateWidget(format="%Y-%m-%d"),
    )
    filtros_ultimo_cambio_fecha = fields.Field(
        attribute="filtros_ultimo_cambio_fecha",
        column_name="filtros_ultimo_cambio_fecha",
        widget=DateWidget(format="%Y-%m-%d"),
    )
    limpieza_ultima_fecha = fields.Field(
        attribute="limpieza_ultima_fecha",
        column_name="limpieza_ultima_fecha",
        widget=DateWidget(format="%Y-%m-%d"),
    )

    class Meta:
        model = Colectivo
        import_id_fields = ("interno",)
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

        fields = (
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
        )

        export_order = fields

    def before_import_row(self, row, **kwargs):
        if "dominio" in row and row["dominio"] is not None:
            row["dominio"] = str(row["dominio"]).strip().upper()

        if "numero_chasis" not in row:
            row["numero_chasis"] = None

        if row.get("numero_chasis") is not None:
            v = str(row["numero_chasis"]).strip().upper()
            row["numero_chasis"] = v if v else None

    def before_save_instance(self, instance, row, **kwargs):
        if getattr(instance, "numero_chasis", None) is not None:
            v = str(instance.numero_chasis).strip().upper()
            instance.numero_chasis = v if v else None
        else:
            instance.numero_chasis = None

        if getattr(instance, "dominio", None):
            instance.dominio = instance.dominio.strip().upper()