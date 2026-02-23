from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("flota", "0006_alter_colectivo_numero_chasis"),
    ]

    operations = [
        migrations.AddField(
            model_name="colectivo",
            name="matafuego_vto",
            field=models.DateField(blank=True, help_text="Fecha de vencimiento del matafuego de la unidad.", null=True, verbose_name="vencimiento matafuego"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="matafuego_ult_control",
            field=models.DateField(blank=True, help_text="Fecha del último control/recarga del matafuego.", null=True, verbose_name="último control de matafuego"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="odometro_km",
            field=models.PositiveIntegerField(blank=True, help_text="Kilometraje actual estimado. Se usa para alertas de mantenimiento.", null=True, verbose_name="odómetro (km)"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="odometro_fecha",
            field=models.DateField(blank=True, help_text="Fecha en la que se registró el odómetro.", null=True, verbose_name="fecha odómetro"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="aceite_intervalo_km",
            field=models.PositiveIntegerField(blank=True, help_text="Cada cuántos km corresponde cambio de aceite (ej: 10000).", null=True, verbose_name="intervalo aceite (km)"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="aceite_ultimo_cambio_km",
            field=models.PositiveIntegerField(blank=True, help_text="KM del último cambio de aceite.", null=True, verbose_name="último cambio aceite (km)"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="aceite_ultimo_cambio_fecha",
            field=models.DateField(blank=True, null=True, verbose_name="fecha último cambio aceite"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="aceite_obs",
            field=models.TextField(blank=True, default="", help_text="Motivo si se cambió antes de tiempo, observaciones, etc.", verbose_name="observaciones aceite"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="filtros_intervalo_km",
            field=models.PositiveIntegerField(blank=True, help_text="Cada cuántos km corresponde cambio de filtros (ej: 20000).", null=True, verbose_name="intervalo filtros (km)"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="filtros_ultimo_cambio_km",
            field=models.PositiveIntegerField(blank=True, help_text="KM del último cambio de filtros.", null=True, verbose_name="último cambio filtros (km)"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="filtros_ultimo_cambio_fecha",
            field=models.DateField(blank=True, null=True, verbose_name="fecha último cambio filtros"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="filtros_obs",
            field=models.TextField(blank=True, default="", help_text="Motivo si se cambió antes de tiempo, observaciones, etc.", verbose_name="observaciones filtros"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="limpieza_ultima_fecha",
            field=models.DateField(blank=True, help_text="Fecha de la última limpieza registrada.", null=True, verbose_name="última limpieza"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="limpieza_realizada_por",
            field=models.CharField(blank=True, default="", help_text="Texto libre (ej: Empleado X). Luego se puede ligar a usuarios.", max_length=80, verbose_name="limpieza realizada por"),
        ),
        migrations.AddField(
            model_name="colectivo",
            name="limpieza_obs",
            field=models.TextField(blank=True, default="", help_text="Detalle si hubo algo fuera de lo normal.", verbose_name="observaciones limpieza"),
        ),
    ]