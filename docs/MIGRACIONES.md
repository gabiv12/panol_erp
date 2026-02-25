# Migraciones (Inventario + Flota + Adjuntos)

Este proyecto se trabaja en modo local-first. En desarrollo se usa SQLite, pero las reglas aplican igual para MySQL/PostgreSQL.

## Instalación nueva (DB limpia)

Cuando no existe base de datos previa o querés probar una instalación desde cero.

1) Borrar DB local (si corresponde)
- Eliminar `db.sqlite3` (si estás en dev)

2) Migrar normal
```powershell
python manage.py migrate
```

3) Verificar
- Entrar al admin
- Revisar que existan tablas de `inventario_`, `flota_` y `adjuntos_`

## DB existente (ya tenía columnas / se alineó con FAKE)

En algunas máquinas se hizo **alineación** marcando como `--fake` una migración porque la base ya tenía columnas creadas manualmente o por una rama anterior.

Regla práctica:
- Si en tu DB **ya existen** las columnas/tablas que la migración intenta crear, usá `--fake` para marcarla como aplicada.
- Si es una instalación nueva, **NO** uses fake.

Ejemplo típico (caso inventario 0006):
```powershell
python manage.py migrate inventario 0006 --fake
python manage.py migrate
```

Importante:
- `--fake` no crea nada en la DB: solo marca el historial.
- Usalo solo cuando ya verificaste que la estructura existe (por ejemplo, mirando la tabla en SQLite/Workbench).

## Timezone warning en StockActual.last_movement_at

Si alguna vez se grabaron datetimes naive en `inventario_stockactual.last_movement_at`, Django puede mostrar warnings.

Solución:
1) A partir de ahora, el stock_service actualiza `last_movement_at` con `timezone.now()` (aware).
2) Para normalizar lo viejo, corré una vez:

```powershell
python manage.py backfill_stock_last_movement_at
```

Ese comando:
- Completa `last_movement_at` si está NULL (usa updated_at/created_at como fallback)
- Convierte a aware si el valor estaba naive (asume horario local del sistema)
