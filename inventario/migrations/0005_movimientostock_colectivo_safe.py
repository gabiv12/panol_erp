from django.db import migrations, models
import django.db.models.deletion


def _get_column_names(schema_editor, table_name: str) -> set[str]:
    with schema_editor.connection.cursor() as cursor:
        desc = schema_editor.connection.introspection.get_table_description(cursor, table_name)
    # Django devuelve objetos con .name
    return {c.name for c in desc}


def forwards(apps, schema_editor):
    table = "inventario_movimientostock"
    cols = _get_column_names(schema_editor, table)

    # BigAutoField -> bigint (cross-db OK: sqlite/postgres/mysql)
    if "colectivo_id" not in cols:
        schema_editor.execute(f"ALTER TABLE {table} ADD COLUMN colectivo_id bigint NULL")

    # Índice para consultas por unidad + fecha (si ya existe, no falla)
    schema_editor.execute(
        "CREATE INDEX IF NOT EXISTS idx_mov_colectivo_fecha "
        "ON inventario_movimientostock(colectivo_id, fecha)"
    )


def backwards(apps, schema_editor):
    # SQLite no dropea columnas simple. No-op.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0004_ubicacion_layout_safe"),
        ("flota", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(forwards, backwards),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="movimientostock",
                    name="colectivo",
                    field=models.ForeignKey(
                        to="flota.colectivo",
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        blank=True,
                        related_name="movimientos_stock",
                    ),
                ),
            ],
        ),
    ]