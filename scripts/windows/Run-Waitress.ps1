param(
  [Parameter(Mandatory = $true)]
  [string]$ProjectRoot,

  [Alias("Host")]
  [Alias("ListenHost")]
  [string]$BindHost = "127.0.0.1",

  [int]$Port = 8000,

  [string]$LogDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path)) { return }
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "manage.py"))) {
  throw "ProjectRoot invalido: no se encontro manage.py en $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

# Preferir python del venv si existe
$pythonExe = "python"
$venvPy = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPy) { $pythonExe = $venvPy }

# Validar waitress
$hasWaitress = $false
try {
  & $pythonExe -c "import waitress" | Out-Null
  $hasWaitress = $true
} catch {
  $hasWaitress = $false
}

if (-not $hasWaitress) {
  Write-Host "Falta dependencia 'waitress'." -ForegroundColor Yellow
  Write-Host "Instala y reintenta:" -ForegroundColor Yellow
  Write-Host "  python -m pip install waitress" -ForegroundColor Yellow
  exit 2
}

if ([string]::IsNullOrWhiteSpace($LogDir)) {
  $LogDir = Join-Path $ProjectRoot "logs"
}
Ensure-Dir -Path $LogDir

$stamp = Get-Date -Format "yyyyMMdd"
$logFile = Join-Path $LogDir ("server_" + $stamp + ".log")

if (-not $env:DJANGO_DEBUG) { $env:DJANGO_DEBUG = "0" }

$listen = "$BindHost`:$Port"
Write-Host ("Iniciando Waitress en " + $listen)
Write-Host ("Log: " + $logFile)

# Importante:
# En Windows PowerShell 5.1, stdout/stderr de ejecutables nativos puede generar "NativeCommandError"
# aunque el proceso este bien (waitress loggea por stderr).
# Para evitarlo, redirigimos en CMD (no en PowerShell) y asi no se crean error records.
$cmd = '"' + $pythonExe + '" -m waitress --listen=' + $listen + ' config.wsgi:application >> "' + $logFile + '" 2>>&1'
& cmd.exe /c $cmd

# Si waitress se corta, propagar exitcode
if ($LASTEXITCODE -ne 0) {
  throw "Waitress finalizo con exit code $LASTEXITCODE. Ver log: $logFile"
}
