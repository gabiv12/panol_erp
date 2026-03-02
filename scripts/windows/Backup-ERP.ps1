param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [string]$DataDir = "",
  [string]$BackupDir = "",
  [int]$KeepDays = 14
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Ensure-Dir([string]$p){
  if(-not (Test-Path -LiteralPath $p)){
    New-Item -ItemType Directory -Path $p | Out-Null
  }
}

if(-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "manage.py"))){
  throw "ProjectRoot inválido"
}

if([string]::IsNullOrWhiteSpace($DataDir)){
  $DataDir = $ProjectRoot
}
if([string]::IsNullOrWhiteSpace($BackupDir)){
  $BackupDir = Join-Path $ProjectRoot "backups"
}

Ensure-Dir $BackupDir

$db = Join-Path $DataDir "db.sqlite3"
$media = Join-Path $DataDir "media"
$reports = Join-Path $DataDir "reportes"

$stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$zipPath = Join-Path $BackupDir ("backup_" + $stamp + ".zip")

$tmp = Join-Path $env:TEMP ("_erp_backup_" + $stamp)
Ensure-Dir $tmp

if(Test-Path -LiteralPath $db){
  Copy-Item -LiteralPath $db -Destination (Join-Path $tmp "db.sqlite3") -Force
}
if(Test-Path -LiteralPath $media){
  Copy-Item -LiteralPath $media -Destination (Join-Path $tmp "media") -Recurse -Force
}
if(Test-Path -LiteralPath $reports){
  Copy-Item -LiteralPath $reports -Destination (Join-Path $tmp "reportes") -Recurse -Force
}

Compress-Archive -LiteralPath (Join-Path $tmp "*") -DestinationPath $zipPath -Force
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue

Write-Host ("Backup OK: " + $zipPath)

# Retención
$cut = (Get-Date).AddDays(-1 * [Math]::Abs($KeepDays))
Get-ChildItem -LiteralPath $BackupDir -Filter "backup_*.zip" -File |
  Where-Object { $_.LastWriteTime -lt $cut } |
  ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
