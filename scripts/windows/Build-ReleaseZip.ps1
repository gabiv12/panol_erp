[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [string]$ProjectRoot = (Get-Location).Path,

  [Parameter(Mandatory=$false)]
  [string]$Ref = "HEAD",

  [Parameter(Mandatory=$false)]
  [string]$OutZip = (Join-Path $env:USERPROFILE "Downloads\LaTermal_release.zip")
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
  throw "No se encontró .git en ProjectRoot. Usá el repo git para generar el ZIP con git archive."
}

git archive --format zip --output $OutZip $Ref

Write-Host "OK: ZIP generado en: $OutZip"

