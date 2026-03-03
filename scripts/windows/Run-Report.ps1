param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [string]$Period = "daily",
  [string]$OutDir = "",
  [switch]$Send
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path)) { return }
  if (!(Test-Path $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
}

$ProjectRoot = (Resolve-Path $ProjectRoot).Path
if (!(Test-Path (Join-Path $ProjectRoot "manage.py"))) { throw "ProjectRoot inválido: no existe manage.py" }

$venvPy = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $venvPy)) { throw "No existe $venvPy. Creá el venv primero (Install-All.ps1)." }

if ([string]::IsNullOrWhiteSpace($OutDir)) { $OutDir = Join-Path $ProjectRoot "reports" }
Ensure-Dir -Path $OutDir

$sendArg = ""
if ($Send) { $sendArg = "--send" }

Push-Location $ProjectRoot
try {
  & $venvPy manage.py send_report_gerencia --period $Period --outdir $OutDir $sendArg
} finally {
  Pop-Location
}
