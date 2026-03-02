param(
  [string]$TaskName = "LaTermalERP-Reportes"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Tarea eliminada (si existía): $TaskName"
