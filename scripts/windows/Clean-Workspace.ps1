[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [string]$ProjectRoot = (Get-Location).Path,

  [Parameter(Mandatory=$false)]
  [switch]$UpdateGitignore
)

$ErrorActionPreference = "Stop"

function Safe-RemoveDir($path) {
  if (Test-Path $path) {
    Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
  }
}

Set-Location $ProjectRoot

# Python caches
Get-ChildItem -Recurse -Force -Directory -Filter "__pycache__" | ForEach-Object { Safe-RemoveDir $_.FullName }
Get-ChildItem -Recurse -Force -File -Include *.pyc,*.pyo | Remove-Item -Force -ErrorAction SilentlyContinue

# Tool caches
Safe-RemoveDir (Join-Path $ProjectRoot ".pytest_cache")
Safe-RemoveDir (Join-Path $ProjectRoot ".mypy_cache")
Safe-RemoveDir (Join-Path $ProjectRoot ".ruff_cache")

# Patch backups inside project
Get-ChildItem -Directory -Filter "backup_patch_*" -ErrorAction SilentlyContinue | ForEach-Object { Safe-RemoveDir $_.FullName }

# Patch temp dirs in user profile (best-effort)
Get-ChildItem -Directory -Path $env:USERPROFILE -Filter "_tmp_patch_*" -ErrorAction SilentlyContinue | ForEach-Object { Safe-RemoveDir $_.FullName }

Write-Host "OK: limpieza aplicada."

if ($UpdateGitignore) {
  & (Join-Path $ProjectRoot "scripts\windows\Update-Gitignore.ps1") -ProjectRoot $ProjectRoot
}

