from __future__ import annotations

from django.db import migrations, models

from flota.choferes_models import chofer_foto_upload_to, validate_image_size_20mb


class Migration(migrations.Migration):

    dependencies = [
        ("flota", "0015_partes_chofer_fields"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="chofer",
            old_name="flota_chofer_ap_nom_idx",
            new_name="flota_chofe_apellid_c748e7_idx",
        ),
        migrations.RenameIndex(
            model_name="chofer",
            old_name="flota_chofer_active_idx",
            new_name="flota_chofe_is_acti_95b792_idx",
        ),
        migrations.AlterField(
            model_name="chofer",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="creado el"),
        ),
        migrations.AlterField(
            model_name="chofer",
            name="foto_1",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=chofer_foto_upload_to,
                validators=[validate_image_size_20mb],
                verbose_name="foto 1",
            ),
        ),
        migrations.AlterField(
            model_name="chofer",
            name="foto_2",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=chofer_foto_upload_to,
                validators=[validate_image_size_20mb],
                verbose_name="foto 2",
            ),
        ),
        migrations.AlterField(
            model_name="chofer",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="actualizado el"),
        ),
    ]
