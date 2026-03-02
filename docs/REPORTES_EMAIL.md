# Reportes automáticos por email (Gerencia)

Este proyecto incluye un comando para generar un **informe gerencial** a partir de la Auditoría
y opcionalmente enviarlo por email.

El diseño es **tolerante a internet inestable**:
- Siempre genera archivos locales (TXT + CSV).
- Solo intenta enviar email si se usa `--send` y hay configuración SMTP.

## 1) Generar informe local (sin enviar)
Desde el root del proyecto:

```powershell
python manage.py send_report_gerencia --period daily --outdir reports
```

Genera:
- `informe_<period>_<timestamp>.txt`
- `..._empleados.csv` (resumen por empleado)
- `..._dispositivos.csv` (IP + navegador)
- `..._areas.csv` (uso por módulo)

## 2) Enviar por email (opcional)

### Variables de entorno necesarias

**Ejemplo (PowerShell setx)**

```powershell
setx ERP_SMTP_HOST "smtp.gmail.com"
setx ERP_SMTP_PORT "587"
setx ERP_SMTP_TLS "1"
setx ERP_SMTP_USER "correo@empresa.com"
setx ERP_SMTP_PASS "APP_PASSWORD"
setx ERP_REPORT_FROM "correo@empresa.com"
setx ERP_REPORT_TO "gerente@empresa.com"
```

Abrí una consola nueva y probá:

```powershell
python manage.py send_report_gerencia --period daily --outdir reports --send
```

Notas:
- Si usás Gmail, no uses la clave normal: usá **App Password**.
- Si el internet cae, el comando puede fallar al enviar. Los archivos igual quedan generados.

## 3) Programarlo en Windows (servidor local)

Si ya aplicaste el patch de *Windows Ops*, podés instalar tarea programada:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Install-ReportTask.ps1 -ProjectRoot . -Hour 7 -Minute 0 -Period daily -OutDir "C:\LaTermalERP\data\reportes"
```

Para enviar por email automáticamente (requiere variables ERP_* configuradas en el servidor):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Install-ReportTask.ps1 -ProjectRoot . -Hour 7 -Minute 0 -Period daily -OutDir "C:\LaTermalERP\data\reportes" -Send
```

## 4) Seguridad
- No guardar contraseñas SMTP dentro del repo.
- Usar variables de entorno en el servidor.
- Restringir acceso al servidor por firewall (LAN).
