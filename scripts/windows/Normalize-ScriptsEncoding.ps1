param(
  [string]$ProjectRoot = $null,
  [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
  param([string]$ExplicitRoot)
  if ($ExplicitRoot) {
    return (Resolve-Path -LiteralPath $ExplicitRoot).Path
  }
  $guess = Join-Path $PSScriptRoot "..\.."
  $guess = (Resolve-Path -LiteralPath $guess).Path
  if (Test-Path -LiteralPath (Join-Path $guess "manage.py")) { return $guess }

  $cwd = (Get-Location).Path
  if (Test-Path -LiteralPath (Join-Path $cwd "manage.py")) { return $cwd }

  throw "No se pudo detectar ProjectRoot. Pasa -ProjectRoot con la carpeta donde esta manage.py."
}

function Write-Info($msg) { Write-Host ("[Normalize-ScriptsEncoding] " + $msg) }

function Decode-BytesToText {
  param([byte[]]$Bytes)

  if ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF) {
    return [System.Text.Encoding]::UTF8.GetString($Bytes, 3, $Bytes.Length - 3)
  }

  if ($Bytes.Length -ge 2 -and $Bytes[0] -eq 0xFF -and $Bytes[1] -eq 0xFE) {
    return [System.Text.Encoding]::Unicode.GetString($Bytes, 2, $Bytes.Length - 2)
  }

  if ($Bytes.Length -ge 2 -and $Bytes[0] -eq 0xFE -and $Bytes[1] -eq 0xFF) {
    return [System.Text.Encoding]::BigEndianUnicode.GetString($Bytes, 2, $Bytes.Length - 2)
  }

  try {
    $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
    return $utf8.GetString($Bytes)
  } catch {
    return [System.Text.Encoding]::GetEncoding(1252).GetString($Bytes)
  }
}

function Write-Utf8NoBom {
  param([string]$Path, [string]$Text, [string]$NewLine = "`r`n")
  $normalized = $Text -replace "`r`n", "`n" -replace "`r", "`n"
  if ($NewLine -eq "`r`n") { $normalized = $normalized -replace "`n", "`r`n" }
  $bytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($normalized)
  if ($WhatIf) { Write-Info "WhatIf: escribir UTF-8 sin BOM -> $Path"; return }
  [System.IO.File]::WriteAllBytes($Path, $bytes)
}

function Normalize-LF {
  param([string]$Path, [string]$Text)
  $normalized = $Text -replace "`r`n", "`n" -replace "`r", "`n"
  $bytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($normalized)
  if ($WhatIf) { Write-Info "WhatIf: escribir LF UTF-8 sin BOM -> $Path"; return }
  [System.IO.File]::WriteAllBytes($Path, $bytes)
}

$ProjectRoot = Resolve-ProjectRoot -ExplicitRoot $ProjectRoot

$winDir = Join-Path $ProjectRoot "scripts\windows"
$linDir = Join-Path $ProjectRoot "scripts\linux"

if (-not (Test-Path -LiteralPath $winDir)) { throw "No existe: $winDir" }
if (-not (Test-Path -LiteralPath $linDir)) { Write-Info "Aviso: no existe scripts/linux (se omite)."; $linDir = $null }

Write-Info "ProjectRoot: $ProjectRoot"
Write-Info "Windows:     $winDir"
if ($linDir) { Write-Info "Linux:       $linDir" }

Get-ChildItem -LiteralPath $winDir -Recurse -File |
  Where-Object { $_.Extension -in ".ps1",".bat",".cmd" } |
  ForEach-Object {
    $p = $_.FullName
    $bytes = [System.IO.File]::ReadAllBytes($p)
    $text = Decode-BytesToText -Bytes $bytes
    Write-Utf8NoBom -Path $p -Text $text -NewLine "`r`n"
  }

if ($linDir) {
  Get-ChildItem -LiteralPath $linDir -Recurse -File |
    Where-Object { $_.Extension -eq ".sh" } |
    ForEach-Object {
      $p = $_.FullName
      $bytes = [System.IO.File]::ReadAllBytes($p)
      $text = Decode-BytesToText -Bytes $bytes
      Normalize-LF -Path $p -Text $text
    }
}

Write-Info "OK: normalizacion completada."
