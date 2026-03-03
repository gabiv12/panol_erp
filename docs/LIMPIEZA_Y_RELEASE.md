# Limpieza y release (pendrive) — La Termal

Este documento describe el flujo **offline-first** para generar un ZIP de aplicación y un ZIP de datos, listos para copiar a pendrive y desplegar en el servidor Windows.

## Objetivos

- ZIP de aplicación (código) **sin** datos: sin `db.sqlite3` ni `media/`.
- ZIP de datos (DATA): `db.sqlite3` + `media/`.
- Scripts en Windows con encoding consistente (UTF-8 sin BOM) para evitar fallos por caracteres invisibles.
- Release reproducible, con fallback si no hay `.git`.

## 1) Limpieza del workspace (recomendado)

Desde la raíz del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Clean-Workspace.ps1 -UpdateGitignore
```

## 2) Normalizar encoding de scripts (recomendado)

Esto reescribe **solo encoding/line endings** (no cambia lógica):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Normalize-ScriptsEncoding.ps1
```

Modo prueba:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Normalize-ScriptsEncoding.ps1 -WhatIf
```

## 3) Generar APP ZIP (código)

### Opción A: repositorio con git disponible

Si tenés git y existe `.git`, podés seguir usando el script habitual si ya te funciona.

### Opción B: fallback (sin git / sin `.git`)

Usar el script nuevo de fallback. `-OutZip` es obligatorio:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Build-ReleaseZip-Fallback.ps1 `
  -Ref HEAD `
  -OutZip "D:\LaTermal_app_YYYYMMDD_HHmm.zip"
```

El fallback copia a un staging temporal excluyendo artefactos típicos y luego comprime.

## 4) Generar DATA ZIP (db + media)

Desde la raíz del proyecto:

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmm"
$dst = "D:\LaTermal_data_${ts}.zip"
$temp = Join-Path $env:TEMP ("la_termal_data_" + $ts)
Remove-Item -Recurse -Force $temp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $temp | Out-Null

Copy-Item -Force ".\db.sqlite3" (Join-Path $temp "db.sqlite3")
if (Test-Path ".\media") { Copy-Item -Recurse -Force ".\media" (Join-Path $temp "media") }

if (Test-Path $dst) { Remove-Item -Force $dst }
Compress-Archive -Path (Join-Path $temp "*") -DestinationPath $dst -Force
Remove-Item -Recurse -Force $temp
$dst
```

## 5) Verificación rápida

```powershell
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py send_report_gerencia --period daily --outdir reports
```

## 6) Qué se copia al pendrive

- `LaTermal_app_*.zip`
- `LaTermal_data_*.zip`
- (opcional) `scripts\windows\LaTermal_Deploy_Windows.ps1` para instalar por comando en el servidor.
