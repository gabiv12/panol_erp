from __future__ import annotations

import os
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import migrations, models


def validate_image_size_20mb(f):
    if not f:
        return
    max_bytes = 20 * 1024 * 1024
    if getattr(f, "size", 0) > max_bytes:
        raise ValidationError("La imagen supera 20 MB.")


def chofer_foto_upload_to(instance, filename: str) -> str:
    base, ext = os.path.splitext(filename or "")
    ext = (ext or ".jpg").lower()
    ap = (getattr(instance, "apellido", "") or "chofer").strip().upper().replace(" ", "_")[:30]
    no = (getattr(instance, "nombre", "") or "").strip().upper().replace(" ", "_")[:20]
    return f"choferes/{ap}_{no}/{uuid4().hex}{ext}"


class Migration(migrations.Migration):

    dependencies = [
        ("flota", "0013_salida_programada_diagrama_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="Chofer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("apellido", models.CharField(max_length=60, verbose_name="apellido")),
                ("nombre", models.CharField(max_length=60, verbose_name="nombre")),
                ("legajo", models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name="legajo")),
                ("telefono", models.CharField(blank=True, default="", max_length=30, verbose_name="teléfono")),
                ("observaciones", models.TextField(blank=True, default="", verbose_name="observaciones")),
                ("foto_1", models.ImageField(blank=True, null=True, upload_to=chofer_foto_upload_to, validators=[validate_image_size_20mb], verbose_name="foto 1")),
                ("foto_2", models.ImageField(blank=True, null=True, upload_to=chofer_foto_upload_to, validators=[validate_image_size_20mb], verbose_name="foto 2")),
                ("is_active", models.BooleanField(default=True, verbose_name="activo")),
            ],
            options={"ordering": ["apellido", "nombre", "id"]},
        ),
        migrations.AddIndex(
            model_name="chofer",
            index=models.Index(fields=["apellido", "nombre"], name="flota_chofer_ap_nom_idx"),
        ),
        migrations.AddIndex(
            model_name="chofer",
            index=models.Index(fields=["is_active"], name="flota_chofer_active_idx"),
        ),
    ]
