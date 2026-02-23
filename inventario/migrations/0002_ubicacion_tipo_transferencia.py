from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ubicacion",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("DEPOSITO", "Depósito"),
                    ("TALLER", "Taller"),
                    ("UNIDAD", "Unidad"),
                    ("EXTERNO", "Externo"),
                ],
                default="DEPOSITO",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="ubicacion",
            name="referencia",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddIndex(
            model_name="ubicacion",
            index=models.Index(fields=["tipo"], name="idx_ubicacion_tipo"),
        ),
        migrations.AddField(
            model_name="movimientostock",
            name="ubicacion_destino",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="movimientos_destino",
                to="inventario.ubicacion",
            ),
        ),
        migrations.AlterField(
            model_name="movimientostock",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("INGRESO", "Ingreso"),
                    ("EGRESO", "Egreso"),
                    ("AJUSTE", "Ajuste"),
                    ("TRANSFERENCIA", "Transferencia"),
                ],
                max_length=14,
            ),
        ),
        migrations.AddIndex(
            model_name="movimientostock",
            index=models.Index(fields=["ubicacion_destino", "fecha"], name="idx_mov_destino_fecha"),
        ),
    ]
