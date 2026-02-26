from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flota", "0014_choferes"),
    ]

    operations = [
        migrations.AddField(
            model_name="partediario",
            name="chofer_label",
            field=models.CharField(blank=True, default="", max_length=80, verbose_name="chofer"),
        ),
        migrations.AddField(
            model_name="partediario",
            name="parte_mecanico",
            field=models.TextField(blank=True, default="", verbose_name="parte mecánico"),
        ),
        migrations.AddField(
            model_name="partediario",
            name="parte_electrico",
            field=models.TextField(blank=True, default="", verbose_name="parte eléctrico"),
        ),
        migrations.AddField(
            model_name="partediario",
            name="trabajos_carroceria_varios",
            field=models.TextField(blank=True, default="", verbose_name="carrocería / varios"),
        ),
        migrations.AddField(
            model_name="partediario",
            name="combustible_ruta_detalle",
            field=models.TextField(blank=True, default="", verbose_name="combustible en ruta (detalle)"),
        ),
    ]
