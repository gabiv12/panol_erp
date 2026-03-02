param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [string]$Host = "127.0.0.1",
  [int]$Port = 8000,
  [string]$LogDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Ensure-Dir([string]$p){
  if([string]::IsNullOrWhiteSpace($p)){ return }
  if(-not (Test-Path -LiteralPath $p)){
    New-Item -ItemType Directory -Path $p | Out-Null
  }
}

if(-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "manage.py"))){
  throw "ProjectRoot inválido: no se encontró manage.py en $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

# Activar venv si existe
$venvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if(Test-Path -LiteralPath $venvActivate){
  . $venvActivate
}

# Validar waitress
$hasWaitress = $false
try {
  python -c "import waitress" | Out-Null
  $hasWaitress = $true
} catch {
  $hasWaitress = $false
}

if(-not $hasWaitress){
  Write-Host "Falta dependencia 'waitress'. Instalá y reintentá:" -ForegroundColor Yellow
  Write-Host "  python -m pip install waitress" -ForegroundColor Yellow
  exit 2
}

# Logs
if([string]::IsNullOrWhiteSpace($LogDir)){
  $LogDir = Join-Path $ProjectRoot "logs"
}
Ensure-Dir $LogDir
$stamp = (Get-Date).ToString("yyyyMMdd")
$logFile = Join-Path $LogDir ("server_" + $stamp + ".log")

# Variables recomendadas (pueden venir del entorno)
if(-not $env:DJANGO_DEBUG){ $env:DJANGO_DEBUG = "0" }

# Ejecutar waitress
$listen = "$Host`:$Port"
Write-Host ("Iniciando Waitress en " + $listen)
Write-Host ("Log: " + $logFile)

# Redirigir stdout/stderr a archivo
python -m waitress --listen=$listen config.wsgi:application *>> $logFile
