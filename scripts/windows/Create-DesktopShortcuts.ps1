param(
  [int]$ServerPort = 8000,
  [string]$ServerHost = "localhost",
  [string]$InstallRoot = "C:\LaTermalERP"
)

$ErrorActionPreference = "Stop"

function Make-Link($path, $target, $args, $desc) {
  $wsh = New-Object -ComObject WScript.Shell
  $lnk = $wsh.CreateShortcut($path)
  $lnk.TargetPath = $target
  if ($args) { $lnk.Arguments = $args }
  if ($desc) { $lnk.Description = $desc }
  $lnk.Save()
}

$publicDesktop = [Environment]::GetFolderPath("CommonDesktopDirectory")
$desktop = if ($publicDesktop) { $publicDesktop } else { [Environment]::GetFolderPath("Desktop") }

$url = "http://$ServerHost`:$ServerPort/dashboard/"
$reportsDir = Join-Path (Join-Path $InstallRoot "data") "reportes"

Make-Link -path (Join-Path $desktop "La Termal ERP - Dashboard.lnk") -target "explorer.exe" -args $url -desc "Abrir Dashboard de La Termal ERP"
Make-Link -path (Join-Path $desktop "La Termal ERP - Reportes.lnk") -target "explorer.exe" -args $reportsDir -desc "Abrir carpeta de reportes gerenciales"

Write-Host "Accesos creados en: $desktop"
