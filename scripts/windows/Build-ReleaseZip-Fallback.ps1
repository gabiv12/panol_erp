param(
  [Parameter(Mandatory = $true)]
  [string]$OutZip,

  [string]$Ref = "HEAD",

  [string]$ProjectRoot = $null,

  [switch]$IncludeRequirementsCache
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
  param([string]$ExplicitRoot)
  if ($ExplicitRoot) {
    return (Resolve-Path -LiteralPath $ExplicitRoot).Path
  }

  # Default: scripts\windows\ -> project root is 2 levels up
  $guess = Join-Path $PSScriptRoot "..\.."
  $guess = (Resolve-Path -LiteralPath $guess).Path

  if (Test-Path -LiteralPath (Join-Path $guess "manage.py")) { return $guess }

  # Fallback: current directory if it looks like a Django project
  $cwd = (Get-Location).Path
  if (Test-Path -LiteralPath (Join-Path $cwd "manage.py")) { return $cwd }

  throw "No se pudo detectar ProjectRoot. Pasa -ProjectRoot con la carpeta donde esta manage.py."
}

function Ensure-ParentDir {
  param([string]$Path)
  $parent = Split-Path -Parent $Path
  if (-not $parent) { throw "OutZip invalido (sin carpeta): $Path" }
  if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent | Out-Null
  }
}

function New-TempDir {
  $root = Join-Path $env:TEMP ("la_termal_release_" + (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + [Guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $root | Out-Null
  return $root
}

function Invoke-Robocopy {
  param(
    [string]$Source,
    [string]$Dest,
    [string[]]$XD,
    [string[]]$XF
  )

  New-Item -ItemType Directory -Path $Dest -Force | Out-Null

  $args = @(
    $Source,
    $Dest,
    "/E",              # include subdirs, incl empty
    "/NFL","/NDL","/NJH","/NJS","/NP",
    "/R:2","/W:1"
  )

  if ($XD -and $XD.Count -gt 0) { $args += "/XD"; $args += $XD }
  if ($XF -and $XF.Count -gt 0) { $args += "/XF"; $args += $XF }

  $null = & robocopy @args
  # robocopy returns codes: 0-7 are "success" (with variations).
  if ($LASTEXITCODE -ge 8) {
    throw "Robocopy fallo con exit code $LASTEXITCODE"
  }
}

function Write-Info($msg) { Write-Host ("[Build-ReleaseZip-Fallback] " + $msg) }

$ProjectRoot = Resolve-ProjectRoot -ExplicitRoot $ProjectRoot

# Normalizar OutZip sin depender de que exista la carpeta (evita Resolve-Path con cadenas vacias)
$OutZip = [System.IO.Path]::GetFullPath($OutZip)

if (-not ($OutZip.ToLower().EndsWith(".zip"))) {
  throw "-OutZip debe terminar en .zip. Recibido: $OutZip"
}

Ensure-ParentDir -Path $OutZip

Write-Info "ProjectRoot: $ProjectRoot"
Write-Info "Ref:        $Ref"
Write-Info "OutZip:     $OutZip"

$hasGit = $false
try { $null = Get-Command git -ErrorAction Stop; $hasGit = $true } catch { $hasGit = $false }

$gitDir = Join-Path $ProjectRoot ".git"
$useGitArchive = $hasGit -and (Test-Path -LiteralPath $gitDir)

if ($useGitArchive) {
  Write-Info "Modo: git archive (repositorio detectado)."
  & git -C $ProjectRoot archive --format=zip $Ref -o $OutZip
  Write-Info "OK: ZIP generado con git archive."
  exit 0
}

Write-Info "Modo: fallback (sin git/.git). Copia a staging + Compress-Archive."

$tmp = New-TempDir
$staging = Join-Path $tmp "staging"
New-Item -ItemType Directory -Path $staging | Out-Null

# Excluir artefactos comunes (los datos van en DATA ZIP separado)
$xd = @(
  ".git",
  ".venv","venv",
  "node_modules",
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  ".idea",
  ".vscode",
  "dist","build",
  "reports",
  "backups",
  "_patch_backups"
)

$xf = @(
  "db.sqlite3",
  "*.zip",
  "*.log",
  "*.tmp",
  "*.pyc",
  "*.pyo"
)

Invoke-Robocopy -Source $ProjectRoot -Dest $staging -XD $xd -XF $xf

# Si media quedo copiado por estructura, removerlo (DATA ZIP lo contiene)
$mediaPath = Join-Path $staging "media"
if (Test-Path -LiteralPath $mediaPath) {
  Remove-Item -Recurse -Force -LiteralPath $mediaPath
}

if (Test-Path -LiteralPath $OutZip) { Remove-Item -Force -LiteralPath $OutZip }
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $OutZip -Force

Write-Info "OK: ZIP generado por fallback."
try { Remove-Item -Recurse -Force -LiteralPath $tmp } catch { }
