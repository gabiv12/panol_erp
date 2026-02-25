param(
  [Parameter(Mandatory=$false)]
  [string]$ProjectRoot = ".",
  [Parameter(Mandatory=$false)]
  [string]$ShortcutName = "La Termal ERP - Iniciar",
  [Parameter(Mandatory=$false)]
  [ValidateSet("Local","LAN")]
  [string]$Mode = "Local"
)

$ErrorActionPreference = "Stop"

function Resolve-FullPath([string]$p) {
  try { return (Resolve-Path -LiteralPath $p).Path } catch { return [System.IO.Path]::GetFullPath($p) }
}

$ProjectRootAbs = Resolve-FullPath $ProjectRoot
if (-not (Test-Path -LiteralPath $ProjectRootAbs)) { throw "No existe ProjectRoot: $ProjectRootAbs" }

$batName = if ($Mode -eq "LAN") { "LaTermalERP_Iniciar_LAN.bat" } else { "LaTermalERP_Iniciar.bat" }
$batPath = Join-Path $ProjectRootAbs $batName

if (-not (Test-Path -LiteralPath $batPath)) {
  throw "No existe el .bat: $batPath`nCopie $batName dentro del proyecto (misma carpeta que manage.py)."
}

$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop ($ShortcutName + ".lnk")

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($lnkPath)
$sc.TargetPath = $batPath
$sc.WorkingDirectory = $ProjectRootAbs
$sc.WindowStyle = 1
$sc.Description = "Inicia La Termal ERP (servidor local)"
$sc.Save()

Write-Host "Acceso directo creado en: $lnkPath"
Write-Host "Modo: $Mode"
