from django.db import migrations

def _colnames(cursor, table_name: str):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}

def _indexnames(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    return {row[0] for row in cursor.fetchall()}

def forwards(apps, schema_editor):
    # Works on SQLite and is safe to re-run (checks existing columns)
    with schema_editor.connection.cursor() as cursor:
        cols = _colnames(cursor, "inventario_ubicacion")

        # --- Ubicacion layout fields ---
        if "padre_id" not in cols:
            cursor.execute("ALTER TABLE inventario_ubicacion ADD COLUMN padre_id integer NULL")
        if "pasillo" not in cols:
            cursor.execute("ALTER TABLE inventario_ubicacion ADD COLUMN pasillo varchar(20) NOT NULL DEFAULT ''")
        if "modulo" not in cols:
            cursor.execute("ALTER TABLE inventario_ubicacion ADD COLUMN modulo smallint NULL")
        if "nivel" not in cols:
            cursor.execute("ALTER TABLE inventario_ubicacion ADD COLUMN nivel smallint NULL")
        if "posicion" not in cols:
            cursor.execute("ALTER TABLE inventario_ubicacion ADD COLUMN posicion smallint NULL")
        if "permite_transferencias" not in cols:
            cursor.execute("ALTER TABLE inventario_ubicacion ADD COLUMN permite_transferencias bool NOT NULL DEFAULT 1")

        # Index for parent lookups (optional)
        idxs = _indexnames(cursor)
        if "idx_ubicacion_padre" not in idxs:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ubicacion_padre ON inventario_ubicacion(padre_id)")

def backwards(apps, schema_editor):
    # SQLite can't easily drop columns; keep as no-op.
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("inventario", "0003_alter_ubicacion_referencia"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
