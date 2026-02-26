from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

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
        help_text="NÃºmero interno de la unidad (identificador operativo).",
    )

    dominio = models.CharField(
        "dominio (patente)",
        max_length=12,
        unique=True,
        help_text="Dominio/patente. Se recomienda cargar en mayÃºsculas.",
    )

    anio_modelo = models.PositiveIntegerField(
        "aÃ±o modelo",
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
    )

    marca = models.CharField("marca (chasis)", max_length=40)
    modelo = models.CharField("modelo (chasis)", max_length=60)

    # IMPORTANTE:
    # - NULL/blank para permitir importar CSV sin chasis.
    # - SQLite permite mÃºltiples NULL aunque sea UNIQUE.
    numero_chasis = models.CharField(
        "nÃºmero de chasis",
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        help_text="NÃºmero/VIN del chasis. Puede cargarse despuÃ©s; si está vacÃ­o no se valida unicidad.",
    )

    carroceria_marca = models.CharField(
        "carrocerÃ­a (marca)",
        max_length=60,
        blank=True,
        default="",
    )

    revision_tecnica_vto = models.DateField(
        "vencimiento revisiÃ³n tÃ©cnica",
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
    matafuego_1_vto = models.DateField(
        "vencimiento matafuego 1",
        blank=True,
        null=True,
        help_text="Fecha de vencimiento del matafuego 1 de la unidad.",
    )
    matafuego_2_vto = models.DateField(
        "vencimiento matafuego 2",
        blank=True,
        null=True,
        help_text="Fecha de vencimiento del matafuego 2 de la unidad.",
    )
    matafuego_ult_control = models.DateField(
        "Ãºltimo control de matafuego",
        null=True,
        blank=True,
        help_text="Fecha del Ãºltimo control/recarga del matafuego.",
    )

    # ==========================
    # Mantenimiento por KM
    # ==========================
    odometro_km = models.PositiveIntegerField(
        "odÃ³metro (km)",
        null=True,
        blank=True,
        help_text="Kilometraje actual estimado. Se usa para alertas de mantenimiento.",
    )
    odometro_fecha = models.DateField(
        "fecha odÃ³metro",
        null=True,
        blank=True,
        help_text="Fecha en la que se registrÃ³ el odÃ³metro.",
    )

    aceite_intervalo_km = models.PositiveIntegerField(
        "intervalo aceite (km)",
        null=True,
        blank=True,
        help_text="Cada cuÃ¡ntos km corresponde cambio de aceite (ej: 10000).",
    )
    aceite_ultimo_cambio_km = models.PositiveIntegerField(
        "Ãºltimo cambio aceite (km)",
        null=True,
        blank=True,
        help_text="KM del Ãºltimo cambio de aceite.",
    )
    aceite_ultimo_cambio_fecha = models.DateField(
        "fecha Ãºltimo cambio aceite",
        null=True,
        blank=True,
    )
    aceite_obs = models.TextField(
        "observaciones aceite",
        blank=True,
        default="",
        help_text="Motivo si se cambiÃ³ antes de tiempo, observaciones, etc.",
    )

    filtros_intervalo_km = models.PositiveIntegerField(
        "intervalo filtros (km)",
        null=True,
        blank=True,
        help_text="Cada cuÃ¡ntos km corresponde cambio de filtros (ej: 20000).",
    )
    filtros_ultimo_cambio_km = models.PositiveIntegerField(
        "Ãºltimo cambio filtros (km)",
        null=True,
        blank=True,
        help_text="KM del Ãºltimo cambio de filtros.",
    )
    filtros_ultimo_cambio_fecha = models.DateField(
        "fecha Ãºltimo cambio filtros",
        null=True,
        blank=True,
    )
    filtros_obs = models.TextField(
        "observaciones filtros",
        blank=True,
        default="",
        help_text="Motivo si se cambiÃ³ antes de tiempo, observaciones, etc.",
    )

    # ==========================
    # Limpieza (registro simple)
    # ==========================
    limpieza_ultima_fecha = models.DateField(
        "Ãºltima limpieza",
        null=True,
        blank=True,
        help_text="Fecha de la Ãºltima limpieza registrada.",
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
        "jurisdicciÃ³n",
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
    matafuego_vencimiento_2 = models.DateField(
        null=True,
        blank=True,
        verbose_name="Vencimiento matafuego 2",
        help_text="Fecha de vencimiento del matafuego 2 de la unidad.",
    )

    class Meta:
        verbose_name = "colectivo"
        verbose_name_plural = "colectivos"
        ordering = ["interno"]
        permissions = [
            ("can_import_colectivos", "Puede importar colectivos (CSV)"),
            ("can_export_colectivos", "Puede exportar colectivos (CSV)"),
        ]
    @property
    def matafuego_proximo_vencimiento(self):
        """Próximo vencimiento (mínimo) entre matafuego 1 y 2.

        Compatibilidad:
        - Si no hay datos en campos nuevos, usa los legacy (matafuego_vto y matafuego_vencimiento_2).
        """
        v1 = self.matafuego_1_vto or self.matafuego_vto
        v2 = self.matafuego_2_vto or getattr(self, "matafuego_vencimiento_2", None)

        fechas = [d for d in (v1, v2) if d]
        return min(fechas) if fechas else None
    @property
    def matafuego_dias_restantes(self):
        # DÃ­as restantes al prÃ³ximo vencimiento (negativo si está vencido).
        vto = self.matafuego_proximo_vencimiento
        if not vto:
            return None
        return (vto - timezone.localdate()).days

    def __str__(self):
        return f"Interno {self.interno} - {self.dominio}"

    def clean(self):
        """
        Normalizaciones seguras para evitar:
        - dominios con minÃºsculas/espacios
        - chasis vacÃ­o que choque por UNIQUE ("" vs NULL)
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


class SalidaProgramada(TimeStampedModel):
    class Tipo(models.TextChoices):
        NORMAL = "NORMAL", "Normal"
        ESPECIAL = "ESPECIAL", "Especial"

    class Estado(models.TextChoices):
        PROGRAMADA = "PROGRAMADA", "Programada"
        EN_CURSO = "EN_CURSO", "En curso"
        FINALIZADA = "FINALIZADA", "Finalizada"
        CANCELADA = "CANCELADA", "Cancelada"

    colectivo = models.ForeignKey(
        "flota.Colectivo",
        on_delete=models.PROTECT,
        related_name="salidas_programadas",
    )

    salida_programada = models.DateTimeField("salida programada")
    llegada_programada = models.DateTimeField("llegada programada", null=True, blank=True)

    salida_real = models.DateTimeField("salida real", null=True, blank=True)
    llegada_real = models.DateTimeField("llegada real", null=True, blank=True)

    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.NORMAL)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PROGRAMADA)

    seccion = models.CharField(
    "sección",
    max_length=80,
    blank=True,
    default="",
    help_text="Grupo del diagrama (ej: SÁENZ PEÑA - RESISTENCIA).",
    )

    salida_label = models.CharField(
        "etiqueta de salida",
        max_length=50,
        blank=True,
        default="",
        help_text="Texto corto como en el diagrama en papel (ej: 05:00 DIRECTO / RCIA 06:00HS DIRECTO).",
    )

    regreso = models.CharField(
        "regreso",
        max_length=40,
        blank=True,
        default="",
        help_text="Hora/leyenda de regreso (ej: 12:00 DIR / 09:00 INT / **).",
    )

    chofer = models.CharField("chofer", max_length=80, blank=True, default="")
    recorrido = models.CharField("recorrido", max_length=120, blank=True, default="")
    nota = models.CharField("nota", max_length=160, blank=True, default="")

    class Meta:
        ordering = ["salida_programada", "id"]
        indexes = [
            models.Index(fields=["salida_programada"], name="idx_salida_prog_fecha"),
            models.Index(fields=["seccion", "salida_programada"], name="idx_salida_prog_seccion"),
            models.Index(fields=["colectivo", "salida_programada"], name="idx_salida_prog_colectivo"),
        ]

    def __str__(self) -> str:
        return f"Salida {self.id} - {self.colectivo_id} - {self.salida_programada:%Y-%m-%d %H:%M}"



from .choferes_models import Chofer  # noqa: F401

