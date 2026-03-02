param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [string]$DataDir = "",
  [string]$BackupDir = "",
  [int]$KeepDays = 14,
  [int]$Hour = 2,
  [int]$Minute = 0,
  [string]$TaskName = "LaTermalERP-Backup"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if([string]::IsNullOrWhiteSpace($DataDir)){ $DataDir = $ProjectRoot }
if([string]::IsNullOrWhiteSpace($BackupDir)){ $BackupDir = Join-Path $ProjectRoot "backups" }

$script = Join-Path $ProjectRoot "scripts\windows\Backup-ERP.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`" -ProjectRoot `"$ProjectRoot`" -DataDir `"$DataDir`" -BackupDir `"$BackupDir`" -KeepDays $KeepDays"
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($Hour).AddMinutes($Minute))
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "SYSTEM" -Force | Out-Null
Write-Host "Tarea instalada: $TaskName (diaria $Hour:$('{0:00}' -f $Minute))"
