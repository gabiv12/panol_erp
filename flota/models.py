from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from core.models import TimeStampedModel


class Colectivo(TimeStampedModel):
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        TALLER = "TALLER", "En taller"
        BAJA = "BAJA", "Baja"

    class TipoServicio(models.TextChoices):
        MEDIA_DISTANCIA = "MEDIA_DISTANCIA", "Media Distancia"
        URBANO = "URBANO", "Urbano"
        INTERURBANO = "INTERURBANO", "Interurbano"

    interno = models.PositiveIntegerField(
        "interno",
        unique=True,
        validators=[MinValueValidator(1)],
        help_text="Número interno de la unidad (identificador operativo).",
    )

    dominio = models.CharField(
        "dominio (patente)",
        max_length=12,
        unique=True,
        help_text="Dominio/patente. Se recomienda cargar en mayúsculas.",
    )

    anio_modelo = models.PositiveIntegerField(
        "año modelo",
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
    )

    marca = models.CharField("marca (chasis)", max_length=40)
    modelo = models.CharField("modelo (chasis)", max_length=60)

    # IMPORTANTE:
    # - NULL/blank para permitir importar CSV sin chasis.
    # - SQLite permite múltiples NULL aunque sea UNIQUE.
    numero_chasis = models.CharField(
        "número de chasis",
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        help_text="Número/VIN del chasis. Puede cargarse después; si está vacío no se valida unicidad.",
    )

    carroceria_marca = models.CharField(
        "carrocería (marca)",
        max_length=60,
        blank=True,
        default="",
    )

    revision_tecnica_vto = models.DateField(
        "vencimiento revisión técnica",
        null=True,
        blank=True,
    )

    # ==========================
    # Seguridad / Matafuegos
    # ==========================
    matafuego_vto = models.DateField(
        "vencimiento matafuego",
        null=True,
        blank=True,
        help_text="Fecha de vencimiento del matafuego de la unidad.",
    )
    matafuego_ult_control = models.DateField(
        "último control de matafuego",
        null=True,
        blank=True,
        help_text="Fecha del último control/recarga del matafuego.",
    )

    # ==========================
    # Mantenimiento por KM
    # ==========================
    odometro_km = models.PositiveIntegerField(
        "odómetro (km)",
        null=True,
        blank=True,
        help_text="Kilometraje actual estimado. Se usa para alertas de mantenimiento.",
    )
    odometro_fecha = models.DateField(
        "fecha odómetro",
        null=True,
        blank=True,
        help_text="Fecha en la que se registró el odómetro.",
    )

    aceite_intervalo_km = models.PositiveIntegerField(
        "intervalo aceite (km)",
        null=True,
        blank=True,
        help_text="Cada cuántos km corresponde cambio de aceite (ej: 10000).",
    )
    aceite_ultimo_cambio_km = models.PositiveIntegerField(
        "último cambio aceite (km)",
        null=True,
        blank=True,
        help_text="KM del último cambio de aceite.",
    )
    aceite_ultimo_cambio_fecha = models.DateField(
        "fecha último cambio aceite",
        null=True,
        blank=True,
    )
    aceite_obs = models.TextField(
        "observaciones aceite",
        blank=True,
        default="",
        help_text="Motivo si se cambió antes de tiempo, observaciones, etc.",
    )

    filtros_intervalo_km = models.PositiveIntegerField(
        "intervalo filtros (km)",
        null=True,
        blank=True,
        help_text="Cada cuántos km corresponde cambio de filtros (ej: 20000).",
    )
    filtros_ultimo_cambio_km = models.PositiveIntegerField(
        "último cambio filtros (km)",
        null=True,
        blank=True,
        help_text="KM del último cambio de filtros.",
    )
    filtros_ultimo_cambio_fecha = models.DateField(
        "fecha último cambio filtros",
        null=True,
        blank=True,
    )
    filtros_obs = models.TextField(
        "observaciones filtros",
        blank=True,
        default="",
        help_text="Motivo si se cambió antes de tiempo, observaciones, etc.",
    )

    # ==========================
    # Limpieza (registro simple)
    # ==========================
    limpieza_ultima_fecha = models.DateField(
        "última limpieza",
        null=True,
        blank=True,
        help_text="Fecha de la última limpieza registrada.",
    )
    limpieza_realizada_por = models.CharField(
        "limpieza realizada por",
        max_length=80,
        blank=True,
        default="",
        help_text="Texto libre (ej: Empleado X). Luego se puede ligar a usuarios.",
    )
    limpieza_obs = models.TextField(
        "observaciones limpieza",
        blank=True,
        default="",
        help_text="Detalle si hubo algo fuera de lo normal.",
    )

    tiene_gps = models.BooleanField("tiene GPS", default=False)
    usa_biodiesel = models.BooleanField("usa biodiesel", default=False)

    tipo_servicio = models.CharField(
        "tipo de servicio",
        max_length=20,
        choices=TipoServicio.choices,
        default=TipoServicio.MEDIA_DISTANCIA,
    )

    jurisdiccion = models.CharField(
        "jurisdicción",
        max_length=80,
        default="Chaco",
        help_text="Base principal. Puede ampliarse a futuro (otras provincias).",
    )

    estado = models.CharField(
        "estado",
        max_length=10,
        choices=Estado.choices,
        default=Estado.ACTIVO,
    )

    observaciones = models.TextField("observaciones", blank=True, default="")
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "colectivo"
        verbose_name_plural = "colectivos"
        ordering = ["interno"]
        permissions = [
            ("can_import_colectivos", "Puede importar colectivos (CSV)"),
            ("can_export_colectivos", "Puede exportar colectivos (CSV)"),
        ]

    def __str__(self):
        return f"Interno {self.interno} - {self.dominio}"

    def clean(self):
        """
        Normalizaciones seguras para evitar:
        - dominios con minúsculas/espacios
        - chasis vacío que choque por UNIQUE ("" vs NULL)
        """
        if self.dominio:
            self.dominio = self.dominio.strip().upper()

        if self.numero_chasis:
            v = self.numero_chasis.strip().upper()
            self.numero_chasis = v if v else None
        else:
            self.numero_chasis = None

        if self.limpieza_realizada_por:
            self.limpieza_realizada_por = self.limpieza_realizada_por.strip()

# Partes diarios (modelos extra)
from .partes_models import ParteDiario, ParteDiarioAdjunto  # noqa: F401
