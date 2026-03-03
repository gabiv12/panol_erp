param(
  [Parameter(Mandatory = $true)]
  [string]$ProjectRoot,

  [Alias("Host")]
  [Alias("ListenHost")]
  [string]$BindHost = "0.0.0.0",

  [int]$Port = 8000,

  [string]$LogDir = "",

  [string]$TaskName = "LaTermalERP-Server"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $p  = New-Object Security.Principal.WindowsPrincipal($id)
  return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Assert-Admin)) {
  throw "Acceso denegado. Abri PowerShell como Administrador para instalar la tarea."
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "manage.py"))) {
  throw "ProjectRoot invalido: no se encontro manage.py en $ProjectRoot"
}

if ([string]::IsNullOrWhiteSpace($LogDir)) {
  $LogDir = Join-Path $ProjectRoot "logs"
}

$script = Join-Path $ProjectRoot "scripts\windows\Run-Waitress.ps1"

# Ejecuta waitress al arrancar. Se mantiene -Host por compatibilidad (alias en Run-Waitress).
$arg = @(
  "-NoProfile",
  "-ExecutionPolicy", "Bypass",
  "-File", "`"$script`"",
  "-ProjectRoot", "`"$ProjectRoot`"",
  "-Host", "`"$BindHost`"",
  "-Port", $Port,
  "-LogDir", "`"$LogDir`""
) -join " "

$action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Registrar como SYSTEM (no pide password)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "SYSTEM" -Force | Out-Null

Write-Host "Tarea instalada: $TaskName (inicio automatico al arrancar Windows)"
Write-Host "Para iniciar ahora: Start-ScheduledTask -TaskName `"$TaskName`""
