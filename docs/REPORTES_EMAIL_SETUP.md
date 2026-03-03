# Reportes por email — configuración (Windows)

Este proyecto genera un informe para gerencia desde `manage.py send_report_gerencia`:
- TXT (resumen)
- CSV por empleados
- CSV por dispositivos (IPs / user-agent)
- CSV por áreas (módulos)

## 1) Configuración rápida (recomendada)

Ejecutar **una sola vez** en el servidor Windows (PowerShell Administrador):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Setup-EmailReports.ps1 -ProjectRoot "C:\LaTermalERP\app"
```

El script te pide:
- SMTP (host/puerto/TLS)
- correo usuario + app password
- destinatarios (separados por coma)
- horarios (HH:MM, separados por coma)

Crea tareas programadas:
- `LaTermalERP-Report-0700`
- `LaTermalERP-Report-1900`
(según lo que indiques)

## 2) Variables de entorno usadas

Se guardan a nivel **máquina** (SYSTEM) usando `setx /M`:

- `ERP_SMTP_HOST`
- `ERP_SMTP_PORT`
- `ERP_SMTP_TLS`  (1/0)
- `ERP_SMTP_USER`
- `ERP_SMTP_PASS`
- `ERP_REPORT_FROM`
- `ERP_REPORT_TO`  (lista separada por coma)

> Para que SYSTEM tome los cambios, lo más seguro es reiniciar la PC del servidor.

## 3) Prueba manual (sin esperar la hora)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Run-Report.ps1 -ProjectRoot "C:\LaTermalERP\app" -Period daily -OutDir "C:\LaTermalERP\data\reportes" -Send
```

Si no hay internet, el informe se genera igual en carpeta, y el envío puede fallar sin romper el sistema.
