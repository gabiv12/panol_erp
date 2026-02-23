Hotfix Inventario - Migraciones Layout Ubicaciones

Qué soluciona
- Conflictos de migraciones (múltiples ramas 0003 / merge 0004) y errores de SQLite tipo:
  - duplicate column name: ubicacion_destino_id
  - no such column: inventario_ubicacion.padre_id

Cómo aplicar
1) Copiá el .zip en Descargas.
2) En PowerShell, parado en la raíz del proyecto (panol_erp), ejecutá:

  $PROJ = "C:\Users\gabi\Desktop\2026\panol_erp"
  $ZIP  = "$env:USERPROFILE\Downloads\panol_erp_inventario_migration_hotfix4_patch.zip"
  Expand-Archive -Force $ZIP $PROJ
  cd $PROJ
  powershell -ExecutionPolicy Bypass -File .\apply_inventario_migration_hotfix.ps1

Luego ya podés correr:
  .\.venv\Scripts\python.exe manage.py cargar_layout_ubicaciones --deposito DP --nombre "Depósito Principal" --pasillos A,B --modulos 2 --niveles 3 --posiciones 4

Nota
- El script renombra (deshabilita) migraciones conflictivas agregando sufijo .disabled_YYYYMMDD_HHMMSS_RAND
  para que Django no las tome.
