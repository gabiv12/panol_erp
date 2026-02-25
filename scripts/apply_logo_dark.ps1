param(
  [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Write-Host "== La Termal ERP: Logo oscuro (white) patch =="

# Ensure folders
$staticImg = Join-Path $ProjectRoot "static\img"
New-Item -ItemType Directory -Force -Path $staticImg | Out-Null

# Patch root is .. (because this script lives in ProjectRoot\scripts)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$patchRoot = Split-Path $scriptDir -Parent

# Copy both logos to deterministic names (restores color logo if fue sobrescrito)
$logoColorSrc = Join-Path $patchRoot "static\img\lt_logo.png"
$logoWhiteSrc = Join-Path $patchRoot "static\img\lt_logo_white.png"

$logoColorDst = Join-Path $staticImg "lt_logo.png"
$logoWhiteDst = Join-Path $staticImg "lt_logo_white.png"

if (!(Test-Path $logoColorSrc)) { throw "No encontro logo color en: $logoColorSrc" }
if (!(Test-Path $logoWhiteSrc)) { throw "No encontro logo blanco en: $logoWhiteSrc" }

if ((Resolve-Path $logoColorSrc).Path -ne (Resolve-Path $logoColorDst).Path) {
  Copy-Item $logoColorSrc $logoColorDst -Force
}
if ((Resolve-Path $logoWhiteSrc).Path -ne (Resolve-Path $logoWhiteDst).Path) {
  Copy-Item $logoWhiteSrc $logoWhiteDst -Force
}
Write-Host "OK: Logos copiados a static/img (lt_logo.png y lt_logo_white.png)"

function Ensure-LoadStatic([string]$content) {
  if ($content -match "{%\s*load\s+static\s*%}") { return $content }
  return "{% load static %}`r`n" + $content
}

function Save-Utf8([string]$path, [string]$content) {
  $content | Set-Content -Encoding UTF8 $path
}

# HTML snippet: show color in light mode, white in dark mode
$dualLogo = @'
<div class="relative h-10 w-10">
  <img src="{% static 'img/fondo_blanco.svg' %}" alt="La Termal ERP" class="h-10 w-10 rounded-full bg-white p-1 dark:hidden" />
  <img src="{% static 'img/fondo_oscuro.svg' %}" alt="La Termal ERP" class="h-10 w-10 rounded-full bg-transparent p-0 hidden dark:block" />
</div>
'@

# Sidebar: replace existing single-logo tag or old "PE" avatar block
$sidebar = Join-Path $ProjectRoot "templates\partials\sidebar.html"
if (Test-Path $sidebar) {
  $c = Get-Content $sidebar -Raw
  $c = Ensure-LoadStatic $c

  # Replace "PE" avatar div
  $patternPE = '(?s)<div\s+class="flex\s+h-10\s+w-10[^"]*rounded-full[^"]*">\s*.*?\s*</div>'
  # Replace single img we inserted earlier
  $patternImg = '(?s)<img\s+src="\{\%\s*static\s*''img/lt_logo\.png''\s*\%\}"[^>]*?>'

  if ($c -match $patternImg) {
    # Replace the img with dual block, but keep surrounding layout.
    $c = [regex]::Replace($c, $patternImg, $dualLogo, 1, [System.Text.RegularExpressions.RegexOptions]::Singleline)
  } elseif ($c -match $patternPE) {
    $c = [regex]::Replace($c, $patternPE, $dualLogo, 1, [System.Text.RegularExpressions.RegexOptions]::Singleline)
  }

  Save-Utf8 $sidebar $c
  Write-Host "OK: sidebar.html actualizado (logo cambia con dark mode)"
} else {
  Write-Host "WARNING: No existe $sidebar (omitido)"
}

# Login page: if logo exists, convert to dual
$login = Join-Path $ProjectRoot "templates\auth\login.html"
if (Test-Path $login) {
  $c = Get-Content $login -Raw
  $c = Ensure-LoadStatic $c

  if ($c -match "img/lt_logo\.png" -and $c -notmatch "lt_logo_white\.png") {
    # Replace the first occurrence of the logo img with dual block for larger size
    $dualLogin = @'
<div class="flex justify-center mb-3">
  <div class="relative h-14 w-14">
    <img src="{% static 'img/fondo_blanco.svg' %}" alt="La Termal ERP" class="h-14 w-14 rounded-full bg-white p-1 dark:hidden" />
    <img src="{% static 'img/lt_logo_white.png' %}" alt="La Termal ERP" class="h-14 w-14 rounded-full bg-transparent p-0 hidden dark:block" />
  </div>
</div>
'@
    $c = [regex]::Replace($c, '(?s)<div class="flex justify-center mb-3">.*?<img[^>]*img/lt_logo\.png[^>]*>.*?</div>', $dualLogin, 1, [System.Text.RegularExpressions.RegexOptions]::Singleline)
  }

  Save-Utf8 $login $c
  Write-Host "OK: login.html actualizado (si tenia logo)"
} else {
  Write-Host "WARNING: No existe $login (omitido)"
}

Write-Host ""
Write-Host "Listo. Verifica:"
Write-Host " - static/img/fondo_blanco.svg (color) y fondo_oscuro.svg (blanco)"
Write-Host " - En modo oscuro se ve el logo blanco."

