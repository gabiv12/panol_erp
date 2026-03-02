<#
Instalación completa (Windows) para servidor local:
- Crea estructura C:\LaTermalERP\{app,data,logs,backups}
- Clona el repo y hace checkout a un tag/branch (por defecto v0.1.1)
- Crea venv, instala deps + waitress
- Migra BD, inicializa roles y auditoría (si existen comandos)
- Configura firewall (opcional) y tareas programadas: server + backups + reportes
- Crea accesos directos en el escritorio (opcional)
#>

param(
  [string]$InstallRoot = "C:\LaTermalERP",
  [string]$RepoUrl = "https://github.com/gabiv12/panol_erp.git",
  [string]$Ref = "v0.1.1",
  [string]$Host = "0.0.0.0",
  [int]$Port = 8000,
  [string]$RemoteScope = "LocalSubnet",
  [string]$RemoteAddresses = "",
  [int]$BackupHour = 2,
  [int]$BackupMinute = 0,
  [int]$ReportHour = 7,
  [int]$ReportMinute = 0,
  [string]$ReportPeriod = "daily",
  [switch]$ReportSend,
  [switch]$ConfigureFirewall = $true,
  [switch]$ConfigureTasks = $true,
  [switch]$CreateDesktopShortcuts = $true
)

$ErrorActionPreference = "Stop"

function Write-Info($m) { Write-Host $m }
function Die($m) { throw $m }

function Is-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $p  = New-Object Security.Principal.WindowsPrincipal($id)
  return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Ensure-Cmd($name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { Die "No se encontró '$name' en PATH. Instalalo y reintentá." }
}

$AppDir     = Join-Path $InstallRoot "app"
$DataDir    = Join-Path $InstallRoot "data"
$LogDir     = Join-Path $InstallRoot "logs"
$BackupDir  = Join-Path $InstallRoot "backups"
$ReportsDir = Join-Path $DataDir "reportes"

New-Item -ItemType Directory -Force -Path $AppDir, $DataDir, $LogDir, $BackupDir, $ReportsDir | Out-Null

Write-Info "InstallRoot: $InstallRoot"
Write-Info "AppDir:      $AppDir"
Write-Info "DataDir:     $DataDir"
Write-Info "Logs:        $LogDir"
Write-Info "Backups:     $BackupDir"
Write-Info "Reportes:    $ReportsDir"
Write-Info ""

Ensure-Cmd git
Ensure-Cmd python

if (-not (Test-Path (Join-Path $AppDir ".git"))) {
  Write-Info "Clonando repo..."
  git clone $RepoUrl $AppDir
} else {
  Write-Info "Repo ya existe. Actualizando..."
  Push-Location $AppDir
  git fetch --all --tags
  Pop-Location
}

Push-Location $AppDir
Write-Info "Checkout: $Ref"
git fetch --all --tags
git checkout $Ref

$VenvDir = Join-Path $AppDir ".venv"
if (-not (Test-Path $VenvDir)) {
  Write-Info "Creando venv..."
  python -m venv $VenvDir
}

$Py = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $Py)) { Die "No encontré python del venv: $Py" }

Write-Info "Instalando dependencias..."
& $Py -m pip install --upgrade pip
& $Py -m pip install -r requirements.txt
& $Py -m pip install waitress

if (-not $env:DJANGO_DEBUG)      { Write-Info "Sugerencia: setx /M DJANGO_DEBUG 0" }
if (-not $env:DJANGO_SECRET_KEY) { Write-Info "Sugerencia: setx /M DJANGO_SECRET_KEY 'CLAVE_LARGA_REAL'" }

Write-Info "Migrando base de datos..."
& $Py manage.py migrate

Write-Info "Inicializando roles/auditoría (si aplica)..."
try { & $Py manage.py init_roles   | Out-Null } catch { Write-Info "  (init_roles omitido)" }
try { & $Py manage.py init_auditoria | Out-Null } catch { Write-Info "  (init_auditoria omitido)" }

$admin = Is-Admin
if (($ConfigureTasks -or $ConfigureFirewall) -and (-not $admin)) {
  Write-Info ""
  Write-Info "AVISO: No estás como Administrador. Se omiten firewall/tareas."
  $ConfigureTasks = $false
  $ConfigureFirewall = $false
}

if ($ConfigureFirewall) {
  Write-Info ""
  Write-Info "Configurando firewall..."
  $fw = Join-Path $AppDir "scripts\windows\Firewall-ERP.ps1"
  if (Test-Path $fw) {
    if ($RemoteScope -eq "Custom" -and $RemoteAddresses) {
      powershell -ExecutionPolicy Bypass -File $fw -Port $Port -Scope Custom -RemoteAddresses $RemoteAddresses
    } else {
      powershell -ExecutionPolicy Bypass -File $fw -Port $Port -Scope LocalSubnet
    }
  } else {
    Write-Info "  (Firewall-ERP.ps1 no existe. Omitido)"
  }
}

if ($ConfigureTasks) {
  Write-Info ""
  Write-Info "Instalando tareas programadas..."
  $srv = Join-Path $AppDir "scripts\windows\Install-ServerTask.ps1"
  $bkp = Join-Path $AppDir "scripts\windows\Install-BackupTask.ps1"
  $rep = Join-Path $AppDir "scripts\windows\Install-ReportTask.ps1"

  if (Test-Path $srv) { powershell -ExecutionPolicy Bypass -File $srv -ProjectRoot $AppDir -Host $Host -Port $Port -LogDir $LogDir }
  if (Test-Path $bkp) { powershell -ExecutionPolicy Bypass -File $bkp -ProjectRoot $AppDir -DataDir $DataDir -BackupDir $BackupDir -KeepDays 14 -Hour $BackupHour -Minute $BackupMinute }

  if (Test-Path $rep) {
    if ($ReportSend) {
      powershell -ExecutionPolicy Bypass -File $rep -ProjectRoot $AppDir -Hour $ReportHour -Minute $ReportMinute -Period $ReportPeriod -OutDir $ReportsDir -Send
    } else {
      powershell -ExecutionPolicy Bypass -File $rep -ProjectRoot $AppDir -Hour $ReportHour -Minute $ReportMinute -Period $ReportPeriod -OutDir $ReportsDir
    }
  }
}

if ($CreateDesktopShortcuts) {
  Write-Info ""
  Write-Info "Creando accesos directos..."
  $sc = Join-Path $AppDir "scripts\windows\Create-DesktopShortcuts.ps1"
  if (Test-Path $sc) {
    powershell -ExecutionPolicy Bypass -File $sc -ServerPort $Port -ServerHost "localhost" -InstallRoot $InstallRoot
  } else {
    Write-Info "  (Create-DesktopShortcuts.ps1 no existe. Omitido)"
  }
}

if ($ConfigureTasks -and $admin) {
  try { Start-ScheduledTask -TaskName "LaTermalERP-Server" | Out-Null } catch { }
}

Write-Info ""
Write-Info "Instalación completada."
Write-Info "Probar: http://IP_DEL_SERVIDOR:$Port/dashboard/"
Pop-Location
