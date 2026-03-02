param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [string]$Host = "0.0.0.0",
  [int]$Port = 8000,
  [string]$LogDir = "",
  [string]$TaskName = "LaTermalERP-Server"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if(-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "manage.py"))){
  throw "ProjectRoot inválido: no se encontró manage.py"
}

if([string]::IsNullOrWhiteSpace($LogDir)){
  $LogDir = Join-Path $ProjectRoot "logs"
}

$script = Join-Path $ProjectRoot "scripts\windows\Run-Waitress.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`" -ProjectRoot `"$ProjectRoot`" -Host `"$Host`" -Port $Port -LogDir `"$LogDir`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Registrar como SYSTEM (no requiere contraseña)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "SYSTEM" -Force | Out-Null
Write-Host "Tarea instalada: $TaskName (inicio automático al arrancar Windows)"
Write-Host "Para iniciar ahora: Start-ScheduledTask -TaskName `"$TaskName`""
