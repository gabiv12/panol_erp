# Limpieza del proyecto y armado de ZIP (pendrive)

Objetivo:
- eliminar basura/cachés y carpetas de backups de parches,
- evitar que se suban a git,
- crear un ZIP portable para instalar en otra PC sin internet.

## 1) Limpieza (Windows)

Desde la raíz del proyecto:

```powershell
# borrar caches Python
Get-ChildItem -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Force -File -Include *.pyc,*.pyo | Remove-Item -Force -ErrorAction SilentlyContinue

# borrar caches típicos
Remove-Item -Recurse -Force .pytest_cache,.mypy_cache,.ruff_cache -ErrorAction SilentlyContinue

# borrar backups de parches en el proyecto
Get-ChildItem -Directory -Filter "backup_patch_*" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# borrar temporales de parches en el perfil
Remove-Item -Recurse -Force "$env:USERPROFILE\_tmp_patch_*" -ErrorAction SilentlyContinue
```

Alternativa: usar el script `scripts\windows\Clean-Workspace.ps1`.

## 2) Ignorar basura en git (.gitignore)

Asegurarse de ignorar:
- `backup_patch_*`
- `_tmp_patch_*`
- `reports/`
- `__pycache__/`, `*.pyc`

Podés aplicar automáticamente con:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Update-Gitignore.ps1
```

## 3) ZIP portable (recomendado)

Si querés un ZIP con **solo lo versionado** (sin .git, sin basura):

```powershell
git archive --format zip --output "C:\Users\Usuario\Downloads\LaTermal_v0.1.2.zip" v0.1.2
```

Si querés un ZIP con el estado actual de `main`:

```powershell
git archive --format zip --output "C:\Users\Usuario\Downloads\LaTermal_main.zip" HEAD
```

Alternativa: usar `scripts\windows\Build-ReleaseZip.ps1`.

## 4) Instalación desde pendrive (resumen)

1) Copiar ZIP a la PC servidor y descomprimir en `C:\LaTermal\`.
2) Ejecutar el instalador:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Install-All.ps1 -ProjectRoot "C:\LaTermal"
```

3) Validar:
- `python manage.py test`
- Abrir `http://127.0.0.1:8000/` o `http://IP_DEL_SERVIDOR:8000/` desde otra PC en LAN.

## 5) Interfaz “oculta” para administración rápida
Para carga rápida sin link en menú, usar **Django Admin**:
- URL: `/admin/`
- Solo staff/superuser
- Ideal para “formularios simples” sin crear endpoints nuevos.

