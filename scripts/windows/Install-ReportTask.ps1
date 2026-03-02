param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [int]$Hour = 7,
  [int]$Minute = 0,
  [ValidateSet("daily","weekly","monthly")][string]$Period = "daily",
  [string]$OutDir = "",
  [switch]$Send,
  [string]$TaskName = "LaTermalERP-Reportes"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if([string]::IsNullOrWhiteSpace($OutDir)){
  $OutDir = Join-Path $ProjectRoot "reportes"
}

$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if(-not (Test-Path -LiteralPath $py)){
  $py = "python"
}

$cmd = "manage.py send_report_gerencia --period $Period --outdir `"$OutDir`""
if($Send){ $cmd += " --send" }

$action = New-ScheduledTaskAction -Execute $py -Argument $cmd -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($Hour).AddMinutes($Minute))
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "SYSTEM" -Force | Out-Null
Write-Host "Tarea instalada: $TaskName (diaria $Hour:$('{0:00}' -f $Minute))"
Write-Host "Nota: requiere que exista el comando 'send_report_gerencia' (aplicar patch de reportes)."
