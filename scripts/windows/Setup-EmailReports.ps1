param(
  [string]$ProjectRoot = "",
  [string]$Period = "daily",
  [string]$OutDir = "",
  [string]$Times = "07:00",
  [string]$SmtpHost = "",
  [int]$SmtpPort = 587,
  [switch]$SmtpTls,
  [string]$SmtpUser = "",
  [string]$SmtpPass = "",
  [string]$ReportFrom = "",
  [string]$ReportTo = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
  param([string]$Root)
  if ($Root -and (Test-Path (Join-Path $Root "manage.py"))) { return (Resolve-Path $Root).Path }
  $here = Split-Path -Parent $MyInvocation.MyCommand.Path
  $candidate = Resolve-Path (Join-Path $here "..\..") -ErrorAction SilentlyContinue
  if ($candidate -and (Test-Path (Join-Path $candidate.Path "manage.py"))) { return $candidate.Path }
  throw "No se pudo resolver ProjectRoot. Pasá -ProjectRoot (carpeta que contiene manage.py)."
}

function Prompt-IfEmpty {
  param([string]$Label, [string]$Default = "")
  if ($Default) { $prompt = "$Label [$Default]" } else { $prompt = $Label }
  $v = Read-Host $prompt
  if ([string]::IsNullOrWhiteSpace($v)) { return $Default }
  return $v.Trim()
}

function Set-MachineEnv {
  param([string]$Name, [string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return }
  & setx /M $Name $Value | Out-Null
}

function Ensure-Dir {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path)) { return }
  if (!(Test-Path $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
}

function New-ReportTask {
  param(
    [string]$TaskName,
    [string]$TaskScript,
    [string]$TimeHHMM
  )
  # Replace if exists
  & schtasks /Delete /TN $TaskName /F | Out-Null 2>$null

  $tr = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$TaskScript`" -ProjectRoot `"$ProjectRootResolved`" -Period $Period -OutDir `"$OutDirResolved`" -Send"
  & schtasks /Create /SC DAILY /TN $TaskName /TR $tr /ST $TimeHHMM /RU "SYSTEM" /RL HIGHEST /F | Out-Null
}

$ProjectRootResolved = Resolve-ProjectRoot -Root $ProjectRoot

if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDirResolved = Join-Path $ProjectRootResolved "reports"
} else {
  $OutDirResolved = $OutDir
}
Ensure-Dir -Path $OutDirResolved

Write-Host ""
Write-Host "=== Configuración de reportes por email (La Termal ERP) ==="
Write-Host "Proyecto: $ProjectRootResolved"
Write-Host "Salida informes: $OutDirResolved"
Write-Host ""

if ([string]::IsNullOrWhiteSpace($SmtpHost)) { $SmtpHost = Prompt-IfEmpty -Label "SMTP host" -Default "smtp.gmail.com" }
if ($SmtpPort -le 0) { $SmtpPort = [int](Prompt-IfEmpty -Label "SMTP port" -Default "587") }

if (-not $SmtpTls.IsPresent) {
  $tls = Prompt-IfEmpty -Label "Usar TLS? (1=SI, 0=NO)" -Default "1"
  if ($tls -eq "1") { $SmtpTls = $true } else { $SmtpTls = $false }
}

if ([string]::IsNullOrWhiteSpace($SmtpUser)) { $SmtpUser = Prompt-IfEmpty -Label "SMTP usuario (correo)" }
if ([string]::IsNullOrWhiteSpace($SmtpPass)) { $SmtpPass = Prompt-IfEmpty -Label "SMTP password (App Password recomendado)" }

if ([string]::IsNullOrWhiteSpace($ReportFrom)) { $ReportFrom = $SmtpUser }
if ([string]::IsNullOrWhiteSpace($ReportTo)) { $ReportTo = Prompt-IfEmpty -Label "Destinatarios (separados por coma)" -Default "gerente1@empresa.com,gerente2@empresa.com" }

if ([string]::IsNullOrWhiteSpace($Times)) { $Times = "07:00" }
$Times = Prompt-IfEmpty -Label "Horarios de envío (HH:MM, separados por coma)" -Default $Times

Write-Host ""
Write-Host "Guardando configuración en variables de entorno (máquina)..."

Set-MachineEnv -Name "ERP_SMTP_HOST" -Value $SmtpHost
Set-MachineEnv -Name "ERP_SMTP_PORT" -Value "$SmtpPort"
Set-MachineEnv -Name "ERP_SMTP_TLS" -Value ($(if ($SmtpTls) { "1" } else { "0" }))
Set-MachineEnv -Name "ERP_SMTP_USER" -Value $SmtpUser
Set-MachineEnv -Name "ERP_SMTP_PASS" -Value $SmtpPass
Set-MachineEnv -Name "ERP_REPORT_FROM" -Value $ReportFrom
Set-MachineEnv -Name "ERP_REPORT_TO" -Value $ReportTo

Write-Host "OK. Configuración guardada."
Write-Host ""

$taskScript = Join-Path $ProjectRootResolved "scripts\windows\Run-Report.ps1"
if (!(Test-Path $taskScript)) {
  throw "No existe $taskScript. Asegurate de tener scripts/windows/Run-Report.ps1 en el repo."
}

$timesList = $Times.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -match "^\d{2}:\d{2}$" }
if ($timesList.Count -eq 0) { throw "No se detectaron horarios válidos. Ej: 07:00,19:00" }

Write-Host "Creando tareas programadas..."
foreach ($t in $timesList) {
  $suffix = $t.Replace(":", "")
  $tn = "LaTermalERP-Report-$suffix"
  New-ReportTask -TaskName $tn -TaskScript $taskScript -TimeHHMM $t
  Write-Host "  OK $tn @ $t"
}

Write-Host ""
Write-Host "Listo. Próximo paso recomendado:"
Write-Host "  Reiniciar sesión / reiniciar la PC del servidor (para que SYSTEM tome las variables)."
Write-Host ""
Write-Host "Prueba manual (ahora):"
Write-Host "  powershell -ExecutionPolicy Bypass -File `"$taskScript`" -ProjectRoot `"$ProjectRootResolved`" -Period $Period -OutDir `"$OutDirResolved`" -Send"
