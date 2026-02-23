from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class ParteDiario(models.Model):
    class Tipo(models.TextChoices):
        CHECKLIST = "CHECKLIST", "Checklist"
        INCIDENCIA = "INCIDENCIA", "Incidencia"
        MANTENIMIENTO = "MANTENIMIENTO", "Mantenimiento"
        AUXILIO = "AUXILIO", "Auxilio"

    class Severidad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"
        CRITICA = "CRITICA", "Crítica"

    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        RESUELTO = "RESUELTO", "Resuelto"

    class AccionMantenimiento(models.TextChoices):
        ACEITE = "ACEITE", "Cambio de aceite"
        FILTROS = "FILTROS", "Cambio de filtros"
        LIMPIEZA = "LIMPIEZA", "Limpieza"
        MATAFUEGO = "MATAFUEGO", "Control matafuego"
        OTRO = "OTRO", "Otro"

    colectivo = models.ForeignKey(
        "flota.Colectivo",
        on_delete=models.PROTECT,
        related_name="partes_diarios",
    )
    fecha_evento = models.DateTimeField(default=timezone.now)

    reportado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partes_diarios_reportados",
    )

    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.INCIDENCIA)
    severidad = models.CharField(max_length=10, choices=Severidad.choices, default=Severidad.MEDIA)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.ABIERTO)

    odometro_km = models.PositiveIntegerField(null=True, blank=True)

    # Mantenimiento (si tipo=MANTENIMIENTO)
    accion_mantenimiento = models.CharField(max_length=20, choices=AccionMantenimiento.choices, blank=True, default="")
    km_mantenimiento = models.PositiveIntegerField(null=True, blank=True)
    matafuego_vto_nuevo = models.DateField(null=True, blank=True)

    # Auxilio (si tipo=AUXILIO)
    auxilio_inicio = models.DateTimeField(null=True, blank=True)
    auxilio_fin = models.DateTimeField(null=True, blank=True)

    descripcion = models.TextField()
    observaciones = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_evento", "-id"]
        indexes = [
            models.Index(fields=["colectivo", "fecha_evento"], name="idx_parte_colectivo_fecha"),
            models.Index(fields=["tipo", "estado"], name="idx_parte_tipo_estado"),
        ]

    def __str__(self) -> str:
        return f"Parte {self.id} - {self.colectivo_id} - {self.tipo}"

    @property
    def resumen(self) -> str:
        txt = (self.descripcion or "").strip().replace("\\n", " ")
        return (txt[:120] + "...") if len(txt) > 120 else txt

    @property
    def duracion_auxilio_min(self):
        if not self.auxilio_inicio or not self.auxilio_fin:
            return None
        delta = self.auxilio_fin - self.auxilio_inicio
        return int(delta.total_seconds() // 60)


class ParteDiarioAdjunto(models.Model):
    parte = models.ForeignKey("flota.ParteDiario", on_delete=models.CASCADE, related_name="adjuntos")
    archivo = models.FileField(upload_to="partes_diarios/%Y/%m/%d/")
    descripcion = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Adjunto {self.id} (parte {self.parte_id})"