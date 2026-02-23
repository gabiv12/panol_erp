from __future__ import annotations

import os
import re
from django.db import models
from django.core.validators import FileExtensionValidator


def _safe_slug(s: str) -> str:
    s = (s or "").strip().upper()
    s = re.sub(r"[^A-Z0-9\-_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "SIN-CODIGO"


def producto_imagen_path(instance: "ProductoImagen", filename: str) -> str:
    # Guardado ordenado por código interno del producto
    base, ext = os.path.splitext(filename)
    ext = (ext or "").lower()
    code = _safe_slug(getattr(instance.producto, "codigo", ""))
    return f"productos/{code}/{instance.orden:02d}{ext or '.jpg'}"


class ProductoImagen(models.Model):
    """
    Foto adjunta a un Producto.
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

    def __str__(self) -> str:
        return f"{self.producto.codigo} img#{self.orden}"