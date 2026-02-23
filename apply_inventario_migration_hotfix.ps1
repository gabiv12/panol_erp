# apply_inventario_migration_hotfix.ps1
# Hotfix robusto: deshabilita migraciones conflictivas de inventario (si existen)
# y aplica la migración segura 0004_ubicacion_layout_safe.
# Ejecutar desde la raíz del proyecto:  powershell -ExecutionPolicy Bypass -File .\apply_inventario_migration_hotfix.ps1

$ErrorActionPreference = "Stop"

function Disable-MigrationFile([string]$path) {
  if (Test-Path $path) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $rand  = Get-Random -Minimum 1000 -Maximum 9999
    $leaf  = Split-Path $path -Leaf
    $new   = "$leaf.disabled_${stamp}_${rand}"
    Rename-Item -Path $path -NewName $new -Force
    Write-Host "Deshabilitado: $leaf -> $new"
  }
}

# 1) Deshabilitar migraciones que chocan / duplican columnas
Disable-MigrationFile ".\inventario\migrations\0002_ubicacion_layout_transfer.py"
Disable-MigrationFile ".\inventario\migrations\0002_ubicacion_referencia.py"
Disable-MigrationFile ".\inventario\migrations\0003_ubicacion_referencia.py"

Get-ChildItem ".\inventario\migrations\0004_merge_*.py" -ErrorAction SilentlyContinue | ForEach-Object {
  Disable-MigrationFile $_.FullName
}

# 2) Mostrar estado
Write-Host ""
Write-Host "Estado de migraciones inventario (antes de migrar):"
.\.venv\Scripts\python.exe manage.py showmigrations inventario

# 3) Migrar todo (aplicará 0004_ubicacion_layout_safe si corresponde)
Write-Host ""
Write-Host "Migrando..."
.\.venv\Scripts\python.exe manage.py migrate

Write-Host ""
Write-Host "Listo. Si seguís viendo errores, pegá el output de:"
Write-Host "  - python manage.py showmigrations inventario"
Write-Host "  - python manage.py migrate --plan"
