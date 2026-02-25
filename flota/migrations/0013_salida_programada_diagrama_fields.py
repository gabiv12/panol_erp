from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flota", "0012_salidas_programadas"),
    ]

    operations = [
        migrations.AddField(
            model_name="salidaprogramada",
            name="seccion",
            field=models.CharField(blank=True, default="", help_text="Grupo del diagrama (ej: SÁENZ PEÑA - RESISTENCIA).", max_length=80, verbose_name="sección"),
        ),
        migrations.AddField(
            model_name="salidaprogramada",
            name="salida_label",
            field=models.CharField(blank=True, default="", help_text="Texto corto como en el diagrama en papel (ej: 05:00 DIRECTO / RCIA 06:00HS DIRECTO).", max_length=50, verbose_name="etiqueta de salida"),
        ),
        migrations.AddField(
            model_name="salidaprogramada",
            name="regreso",
            field=models.CharField(blank=True, default="", help_text="Hora/leyenda de regreso (ej: 12:00 DIR / 09:00 INT / **).", max_length=40, verbose_name="regreso"),
        ),
        migrations.AddIndex(
            model_name="salidaprogramada",
            index=models.Index(fields=["seccion", "salida_programada"], name="idx_salida_prog_seccion"),
        ),
    ]
