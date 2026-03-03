# Instalación del servidor (Windows) — La Termal (pendrive)

Este flujo instala/actualiza el servidor en LAN usando:

- APP ZIP: `LaTermal_app_*.zip` (código)
- DATA ZIP: `LaTermal_data_*.zip` (`db.sqlite3` + `media/`)

## Pre-requisitos

- Windows 10/11.
- Python 3.x instalado y accesible como `python`.
- Acceso de Administrador recomendado (firewall y tarea programada).

## Carpeta recomendada

- `C:\LaTermal\app`
- `C:\LaTermal\backups`
- `C:\LaTermal\logs`

## Opción 1: instalación guiada por script (recomendado)

1) Copiá al pendrive los dos ZIP:
   - `LaTermal_app_*.zip`
   - `LaTermal_data_*.zip`

2) En el servidor, abrí PowerShell **como Administrador**.

3) Desde el pendrive (por ejemplo `D:\`), ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File "D:\LaTermal_Deploy_Windows.ps1" `
  -InstallRoot "C:\LaTermal" `
  -Host "0.0.0.0" `
  -Port 8000
```

Notas:
- Si el script no encuentra ZIPs automáticamente, pasá rutas explícitas:
  - `-AppZip "D:\LaTermal_app_YYYYMMDD_HHmm.zip"`
  - `-DataZip "D:\LaTermal_data_YYYYMMDD_HHmm.zip"`
- El script hace backup de app/datos antes de sobrescribir.

## Opción 2: pasos manuales (control total)

1) Extraer APP ZIP en `C:\LaTermal\app`.

2) Backup y restauración de datos:
- Copiar `db.sqlite3` anterior a `C:\LaTermal\backups\pre_restore_YYYYMMDD_HHmmss`.
- Restaurar `db.sqlite3` desde DATA ZIP.
- Restaurar `media\` desde DATA ZIP con `robocopy /MIR`.

3) Entorno:
```powershell
cd C:\LaTermal\app
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\pip.exe install waitress
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py init_roles
```

4) Servicio/tarea y firewall (si existen scripts en `scripts\windows`):
```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Install-ServerTask.ps1 -ProjectRoot C:\LaTermal\app -Host 0.0.0.0 -Port 8000 -LogDir C:\LaTermal\logs
powershell -ExecutionPolicy Bypass -File scripts\windows\Firewall-ERP.ps1 -Port 8000 -Scope LocalSubnet
```

## Validación

- Abrir en el servidor: `http://127.0.0.1:8000/`
- Desde otra PC en LAN: `http://IP_DEL_SERVIDOR:8000/`

Pruebas mínimas por rol:
- Gerente 1: dashboard + auditoría (export).
- Empleado X: horarios + inventario.
- Chofer: solo ver horarios y reportar parte; el resto debe responder 403.

## Troubleshooting rápido

- No abre:
  - Verificar tarea programada corriendo.
  - Verificar firewall (perfil de red privada) y puerto 8000 en LAN.
  - Revisar logs.

- Scripts fallan por encoding:
  - Ejecutar `scripts\windows\Normalize-ScriptsEncoding.ps1` en el repo y regenerar ZIP.
