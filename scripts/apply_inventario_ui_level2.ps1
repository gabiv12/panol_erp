param(
  [Parameter(Mandatory=$true)]
  [string]$ProjectRoot
)

Write-Host "== Inventario UI/UX Nivel 2 Patch =="

if (!(Test-Path $ProjectRoot)) { throw "ProjectRoot no existe: $ProjectRoot" }

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$src  = Join-Path $here ".."  # patch root (unzip mantiene estructura)

# Copiar archivos del patch al proyecto (solo código/templates/static)
robocopy $src $ProjectRoot /E /NFL /NDL /NJH /NJS /R:1 /W:1 | Out-Null

Write-Host "OK: Archivos copiados."
Write-Host ""
Write-Host "Siguiente:"
Write-Host "  1) npm run tw:build"
Write-Host "  2) python manage.py test"
Write-Host "  3) Probar: Inventario > Movimientos > Nuevo movimiento"