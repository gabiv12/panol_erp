param(
  [string]$AppZip = $null,
  [string]$DataZip = $null,

  [string]$InstallRoot = "C:\LaTermal",

  [Alias("Host")]
  [Alias("ListenHost")]
  [string]$BindHost = "0.0.0.0",

  [int]$Port = 8000,

  [switch]$SkipDataRestore,
  [switch]$SkipVenv,
  [switch]$SkipPipInstall,
  [switch]$SkipMigrate,
  [switch]$SkipInitRoles,
  [switch]$SkipTaskInstall,
  [switch]$SkipFirewall,
  [switch]$RunTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host ("[LaTermal-Deploy] " + $msg) }
function Write-Warn($msg) { Write-Host ("[LaTermal-Deploy][WARN] " + $msg) }

function Assert-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $p  = New-Object Security.Principal.WindowsPrincipal($id)
  return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function New-Dir($p) {
  if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

function New-Timestamp { return (Get-Date -Format "yyyyMMdd_HHmmss") }

function Find-LatestZip {
  param([string]$Pattern)
  $drive = (Get-Location).Path.Substring(0,2)
  $root = $drive + "\"
  $z = Get-ChildItem -LiteralPath $root -Filter $Pattern -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if ($z) { return $z.FullName }
  return $null
}

function Backup-Path {
  param([string]$Src, [string]$BackupDir, [string]$Label)
  if (-not (Test-Path -LiteralPath $Src)) { return }
  New-Dir $BackupDir
  $dst = Join-Path $BackupDir ($Label + "_" + (New-Timestamp))
  Write-Info "Backup: $Src -> $dst"
  Copy-Item -Recurse -Force -LiteralPath $Src -Destination $dst
}

function Restore-DataZip {
  param([string]$DataZipPath, [string]$AppDir, [string]$BackupsDir)

  if (-not (Test-Path -LiteralPath $DataZipPath)) { throw "No existe DataZip: $DataZipPath" }

  $tmp = Join-Path $env:TEMP ("la_termal_data_" + (New-Timestamp) + "_" + [Guid]::NewGuid().ToString("N"))
  New-Dir $tmp
  Write-Info "Extrayendo DATA ZIP a temp: $tmp"
  Expand-Archive -LiteralPath $DataZipPath -DestinationPath $tmp -Force

  $dbSrc = Join-Path $tmp "db.sqlite3"
  $mediaSrc = Join-Path $tmp "media"

  if (-not (Test-Path -LiteralPath $dbSrc)) { throw "DATA ZIP no contiene db.sqlite3 en la raiz." }
  if (-not (Test-Path -LiteralPath $mediaSrc)) { Write-Warn "DATA ZIP no contiene carpeta media/ (se omite)." }

  Backup-Path -Src (Join-Path $AppDir "db.sqlite3") -BackupDir $BackupsDir -Label "pre_restore_db"
  Backup-Path -Src (Join-Path $AppDir "media") -BackupDir $BackupsDir -Label "pre_restore_media"

  Copy-Item -Force -LiteralPath $dbSrc -Destination (Join-Path $AppDir "db.sqlite3")

  if (Test-Path -LiteralPath $mediaSrc) {
    $mediaDst = Join-Path $AppDir "media"
    New-Dir $mediaDst
    Write-Info "Restaurando media/ con robocopy /MIR"
    & robocopy $mediaSrc $mediaDst /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Robocopy media fallo (exit $LASTEXITCODE)" }
  }

  try { Remove-Item -Recurse -Force -LiteralPath $tmp } catch { }
}

# Autodeteccion de ZIPs si no se pasan
if (-not $AppZip)  { $AppZip  = Find-LatestZip -Pattern "LaTermal_app_*.zip" }
if (-not $DataZip) { $DataZip = Find-LatestZip -Pattern "LaTermal_data_*.zip" }

if (-not $AppZip) { throw "No se encontro APP ZIP. Pasa -AppZip (ej: D:\LaTermal_app_YYYYMMDD_HHmm.zip)." }
if (-not (Test-Path -LiteralPath $AppZip)) { throw "No existe AppZip: $AppZip" }

$AppDir = Join-Path $InstallRoot "app"
$BackupsDir = Join-Path $InstallRoot "backups"
$LogsDir = Join-Path $InstallRoot "logs"

New-Dir $InstallRoot
New-Dir $AppDir
New-Dir $BackupsDir
New-Dir $LogsDir

Write-Info "InstallRoot: $InstallRoot"
Write-Info "AppZip:      $AppZip"
Write-Info "DataZip:     $DataZip"
Write-Info "AppDir:      $AppDir"
Write-Info "BindHost:    $BindHost"
Write-Info "Port:        $Port"

$admin = Assert-Admin
if (-not $admin) {
  Write-Warn "No estas en PowerShell como Administrador. Se omiten/pueden fallar pasos de firewall y tarea."
}

# Backup app actual antes de sobrescribir
if (Test-Path -LiteralPath (Join-Path $AppDir "manage.py")) {
  Backup-Path -Src $AppDir -BackupDir $BackupsDir -Label "pre_update_app"
}

Write-Info "Extrayendo APP ZIP..."
Expand-Archive -LiteralPath $AppZip -DestinationPath $AppDir -Force

if (-not $SkipDataRestore -and $DataZip -and (Test-Path -LiteralPath $DataZip)) {
  Restore-DataZip -DataZipPath $DataZip -AppDir $AppDir -BackupsDir $BackupsDir
} elseif (-not $SkipDataRestore) {
  Write-Warn "No se restauro DATA (no se encontro DataZip o esta omitido)."
}

$py = "python"

if (-not $SkipVenv) {
  Write-Info "Creando .venv..."
  Push-Location $AppDir
  & $py -m venv ".venv"
  Pop-Location
}

if (-not $SkipPipInstall) {
  Write-Info "Instalando dependencias (pip)..."
  $pip = Join-Path $AppDir ".venv\Scripts\pip.exe"
  if (-not (Test-Path -LiteralPath $pip)) { throw "No existe pip en venv: $pip" }
  & $pip install -r (Join-Path $AppDir "requirements.txt")
  & $pip install waitress
}

if (-not $SkipMigrate) {
  Write-Info "Migraciones..."
  $pyexe = Join-Path $AppDir ".venv\Scripts\python.exe"
  Push-Location $AppDir
  & $pyexe manage.py migrate
  Pop-Location
}

if (-not $SkipInitRoles) {
  Write-Info "Inicializando roles..."
  $pyexe = Join-Path $AppDir ".venv\Scripts\python.exe"
  Push-Location $AppDir
  & $pyexe manage.py init_roles
  Pop-Location
}

if ($RunTests) {
  Write-Info "Ejecutando tests..."
  $pyexe = Join-Path $AppDir ".venv\Scripts\python.exe"
  Push-Location $AppDir
  & $pyexe manage.py test
  Pop-Location
}

if (-not $SkipTaskInstall) {
  $taskScript = Join-Path $AppDir "scripts\windows\Install-ServerTask.ps1"
  if (Test-Path -LiteralPath $taskScript) {
    Write-Info "Instalando tarea programada..."
    & powershell -ExecutionPolicy Bypass -File $taskScript -ProjectRoot $AppDir -Host $BindHost -Port $Port -LogDir $LogsDir
  } else {
    Write-Warn "No existe Install-ServerTask.ps1 en $taskScript (se omite)."
  }
}

if (-not $SkipFirewall -and $admin) {
  $fwScript = Join-Path $AppDir "scripts\windows\Firewall-ERP.ps1"
  if (Test-Path -LiteralPath $fwScript) {
    Write-Info "Configurando firewall (LocalSubnet)..."
    & powershell -ExecutionPolicy Bypass -File $fwScript -Port $Port -Scope LocalSubnet
  } else {
    Write-Warn "No existe Firewall-ERP.ps1 en $fwScript (se omite)."
  }
} elseif (-not $SkipFirewall) {
  Write-Warn "Firewall omitido (no Admin o -SkipFirewall)."
}

Write-Info "OK. Proximo paso: reiniciar PC o iniciar tarea, y abrir http://127.0.0.1:$Port/"
