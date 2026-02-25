param(
  [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

Write-Host "== La Termal ERP Branding Patch =="

# 1) Ensure folders
$staticImg = Join-Path $ProjectRoot "static\img"
New-Item -ItemType Directory -Force -Path $staticImg | Out-Null

# 2) Copy logo from this patch folder to project
$patchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$logoSrc = Join-Path (Split-Path $patchRoot -Parent) "static\img\lt_logo.png"
$logoDst = Join-Path $staticImg "lt_logo.png"

if (!(Test-Path $logoSrc)) { throw "No encontro el logo en: $logoSrc" }
if ((Resolve-Path $logoSrc).Path -ne (Resolve-Path $logoDst).Path) {
  Copy-Item $logoSrc $logoDst -Force
  Write-Host "OK: Logo copiado a $logoDst"
} else {
  Write-Host "OK: Logo ya estaba en destino ($logoDst)"
}
Write-Host "OK: Logo copiado a $logoDst"

function Ensure-LoadStatic([string]$content) {
  if ($content -match "{%\s*load\s+static\s*%}") { return $content }
  return "{% load static %}`r`n" + $content
}

function Save-Utf8([string]$path, [string]$content) {
  $content | Set-Content -Encoding UTF8 $path
}

# 3) Sidebar header (desktop + drawer)
$sidebar = Join-Path $ProjectRoot "templates\partials\sidebar.html"
if (Test-Path $sidebar) {
  $c = Get-Content $sidebar -Raw
  $c = Ensure-LoadStatic $c

  # Replace app name wherever appears
  $c = $c -replace "PaÃ±ol ERP", "La Termal ERP"
  $c = $c -replace "PaÃƒÂ±ol ERP", "La Termal ERP"

  # Replace circular initials block with logo img
  $imgTag = '<img src="{% static ''img/lt_logo.png'' %}" alt="La Termal ERP" class="h-10 w-10 rounded-full bg-white p-1" />'

  $pattern = '(?s)<div\s+class="flex\s+h-10\s+w-10[^"]*rounded-full[^"]*">\s*PE\s*</div>'
  if ($c -match $pattern) {
    $c = [regex]::Replace($c, $pattern, $imgTag, "Singleline")
  } else {
    # Fallback: replace first avatar div of that size
    $pattern2 = '(?s)<div\s+class="flex\s+h-10\s+w-10[^"]*rounded-full[^"]*">\s*.*?\s*</div>'
    $c = [regex]::Replace($c, $pattern2, $imgTag, 1)
  }

  Save-Utf8 $sidebar $c
  Write-Host "OK: Actualizado sidebar.html"
} else {
  Write-Host "WARNING: No existe $sidebar (omitido)"
}

# 4) Login page (optional)
$login = Join-Path $ProjectRoot "templates\auth\login.html"
if (Test-Path $login) {
  $c = Get-Content $login -Raw
  $c = Ensure-LoadStatic $c

  $c = $c -replace "PaÃ±ol ERP", "La Termal ERP"
  $c = $c -replace "PaÃƒÂ±ol ERP", "La Termal ERP"

  if ($c -notmatch "img/lt_logo\.png") {
    $c = $c -replace '(?s)(<div[^>]*class="[^"]*"[^>]*>\s*)(<h1[^>]*>)', ('$1' + '<div class="flex justify-center mb-3"><img src="{% static ''img/lt_logo.png'' %}" alt="La Termal ERP" class="h-14 w-14 rounded-full bg-white p-1" /></div>' + '$2')
  }

  Save-Utf8 $login $c
  Write-Host "OK: Actualizado login.html"
} else {
  Write-Host "WARNING: No existe $login (omitido)"
}

# 5) Replace name in all templates (HTML only)
$templatesRoot = Join-Path $ProjectRoot "templates"
if (Test-Path $templatesRoot) {
  $templates = Get-ChildItem -Path $templatesRoot -Recurse -File -Filter "*.html" -ErrorAction SilentlyContinue
  foreach ($f in $templates) {
    $c = Get-Content $f.FullName -Raw
    $new = $c -replace "PaÃ±ol ERP", "La Termal ERP"
    $new = $new -replace "PaÃƒÂ±ol ERP", "La Termal ERP"
    if ($new -ne $c) {
      Save-Utf8 $f.FullName $new
    }
  }
  Write-Host "OK: Nombre actualizado en templates/*.html"
}

Write-Host ""
Write-Host "Listo. Reinicia el server y verifica:"
Write-Host " - Sidebar con logo + 'La Termal ERP'"
Write-Host " - Login con nombre nuevo"
Write-Host " - Logo en /static/img/lt_logo.png"


