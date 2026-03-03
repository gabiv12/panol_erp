[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$gitignore = Join-Path $ProjectRoot ".gitignore"
if (-not (Test-Path $gitignore)) {
  New-Item -ItemType File -Path $gitignore | Out-Null
}

$lines = @(
  "",
  "# --- La Termal: runtime / patch artifacts (no versionar) ---",
  "backup_patch_*",
  "_tmp_patch_*",
  "_patch_*",
  "reports/",
  "",
  "# Python caches",
  "__pycache__/",
  "*.pyc",
  "*.pyo",
  ".pytest_cache/",
  ".mypy_cache/",
  ".ruff_cache/",
  "",
  "# OS / Editor",
  "Thumbs.db",
  "Desktop.ini",
  ".DS_Store"
)

$current = Get-Content -Path $gitignore -ErrorAction SilentlyContinue
$toAdd = @()
foreach ($l in $lines) {
  if ($l -eq "") { $toAdd += $l; continue }
  if (-not ($current -contains $l)) { $toAdd += $l }
}

if ($toAdd.Count -gt 0) {
  Add-Content -Path $gitignore -Value $toAdd
  Write-Host "OK: .gitignore actualizado (append)."
} else {
  Write-Host "OK: .gitignore ya tenÃ­a las reglas."
}

