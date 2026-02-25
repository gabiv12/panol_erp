param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot
)

$ErrorActionPreference = "Stop"
Write-Host "== Hotfix: Drawer mobile + Movimientos stock =="

# Backup rápido (solo archivos tocados)
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$bk = Join-Path $ProjectRoot ("_backups\hotfix_" + $ts)
New-Item -ItemType Directory -Force -Path $bk | Out-Null

$files = @(
  "static\js\app.js",
  "inventario\views.py"
)

foreach ($rel in $files) {
  $p = Join-Path $ProjectRoot $rel
  if (Test-Path $p) {
    $dst = Join-Path $bk ($rel -replace '[\\/:]','_')
    Copy-Item $p $dst -Force
  }
}

python (Join-Path $ProjectRoot "scripts\patch_hotfix.py") $ProjectRoot

Write-Host "OK: Hotfix aplicado"
Write-Host "Backup en: $bk"
