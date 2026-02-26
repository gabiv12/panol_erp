from __future__ import annotations

import os
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


def validate_image_size_20mb(f):
    """Permite fotos de celular, pero corta casos extremos."""
    if not f:
        return
    max_bytes = 20 * 1024 * 1024
    if getattr(f, "size", 0) > max_bytes:
        raise ValidationError("La imagen supera 20 MB. Usá una foto más liviana o recortala.")


def chofer_foto_upload_to(instance: "Chofer", filename: str) -> str:
    base, ext = os.path.splitext(filename or "")
    ext = (ext or ".jpg").lower()
    safe_ap = (instance.apellido or "chofer").strip().upper().replace(" ", "_")[:30]
    safe_no = (instance.nombre or "").strip().upper().replace(" ", "_")[:20]
    return f"choferes/{safe_ap}_{safe_no}/{uuid4().hex}{ext}"


class Chofer(TimeStampedModel):
    """Catálogo operativo de choferes.

    Compatibilidad:
    - SalidaProgramada.chofer sigue siendo texto (no rompe diagrama legacy).
    - Este catálogo se usa para autocompletar y evitar errores de escritura.
    """

    apellido = models.CharField("apellido", max_length=60)
    nombre = models.CharField("nombre", max_length=60)

    legajo = models.CharField("legajo", max_length=20, null=True, blank=True, unique=True)
    telefono = models.CharField("teléfono", max_length=30, blank=True, default="")
    observaciones = models.TextField("observaciones", blank=True, default="")

    foto_1 = models.ImageField(
        "foto 1",
        upload_to=chofer_foto_upload_to,
        null=True,
        blank=True,
        validators=[validate_image_size_20mb],
    )
    foto_2 = models.ImageField(
        "foto 2",
        upload_to=chofer_foto_upload_to,
        null=True,
        blank=True,
        validators=[validate_image_size_20mb],
    )

    is_active = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["apellido", "nombre", "id"]
        indexes = [
            models.Index(fields=["apellido", "nombre"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        ap = (self.apellido or "").strip().upper()
        no = (self.nombre or "").strip()
        if ap and no:
            return f"{ap}, {no}"
        return (ap or no or "CHOFER").strip()
