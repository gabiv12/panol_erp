from __future__ import annotations

import os
import re

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Max


def _safe_slug(s: str) -> str:
    s = (s or "").strip().upper()
    s = re.sub(r"[^A-Z0-9\-_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "SIN-CODIGO"


def _ensure_orden(instance: "ProductoImagen") -> int:
    """Asegura que `orden` tenga un entero válido.

    Motivo: en el inline formset, `orden` puede venir vacío y convertirse en None.
    El `upload_to` se ejecuta antes del guardado del modelo y no puede formatear None.

    Regla: si no viene `orden`, asignamos el siguiente disponible (MAX + 1) de forma determinística.
    """

    raw = getattr(instance, "orden", None)
    try:
        if raw is not None and str(raw).strip() != "":
            return int(raw)
    except Exception:
        pass

    producto_id = getattr(instance, "producto_id", None)
    if not producto_id:
        instance.orden = 1
        return 1

    try:
        m = instance.__class__.objects.filter(producto_id=producto_id).aggregate(m=Max("orden"))["m"] or 0
        next_orden = int(m) + 1
    except Exception:
        next_orden = 1

    instance.orden = next_orden
    return next_orden


def producto_imagen_path(instance: "ProductoImagen", filename: str) -> str:
    """Path offline-friendly y ordenado por producto + orden."""

    _, ext = os.path.splitext(filename)
    ext = (ext or "").lower() or ".jpg"

    code = _safe_slug(getattr(instance.producto, "codigo", ""))
    orden = _ensure_orden(instance)

    return f"productos/{code}/{orden:02d}{ext}"


class ProductoImagen(models.Model):
    """Foto adjunta a un Producto.

    Se usa FileField para evitar depender de Pillow. Validamos extensión manualmente.
    """

    producto = models.ForeignKey(
        "inventario.Producto",
        on_delete=models.CASCADE,
        related_name="imagenes",
    )

    imagen = models.FileField(
        upload_to=producto_imagen_path,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )

    titulo = models.CharField(max_length=120, blank=True)
    orden = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["orden", "id"]
        indexes = [
            models.Index(fields=["producto", "orden"]),
        ]

    def save(self, *args, **kwargs):
        # Importante: esto ocurre antes de que FileField calcule el upload_to.
        _ensure_orden(self)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        codigo = getattr(self.producto, "codigo", "?")
        return f"{codigo} img#{self.orden}"
