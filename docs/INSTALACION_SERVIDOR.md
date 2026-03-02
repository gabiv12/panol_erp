# Instalación servidor (Windows / Linux) — La Termal ERP

Objetivo: dejar el sistema estable y “difícil de romper” como servidor local.

## Seguridad mínima
- Servidor dedicado (sin WhatsApp/navegación/uso diario).
- Firewall: solo LAN.
- Backups automáticos.
- DEBUG=0 + SECRET_KEY por entorno.
- Usuarios por rol (sin cuentas compartidas).

---

## Windows (instalación automática)
Ejecutar PowerShell **como Administrador**:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
powershell -ExecutionPolicy Bypass -File scripts\windows\Install-All.ps1 -InstallRoot "C:\LaTermalERP" -Ref "v0.1.1"
```

Variables recomendadas (máquina):
```powershell
setx /M DJANGO_DEBUG "0"
setx /M DJANGO_SECRET_KEY "CLAVE_LARGA_REAL"
```

SMTP (opcional):
```powershell
setx /M ERP_SMTP_HOST "smtp.gmail.com"
setx /M ERP_SMTP_PORT "587"
setx /M ERP_SMTP_TLS "1"
setx /M ERP_SMTP_USER "correo@empresa.com"
setx /M ERP_SMTP_PASS "APP_PASSWORD"
setx /M ERP_REPORT_TO "gerente@empresa.com"
setx /M ERP_REPORT_FROM "correo@empresa.com"
```

Accesos directos:
- “La Termal ERP - Dashboard”
- “La Termal ERP - Reportes”

---

## Linux (instalación automática)
Ubuntu/Debian (root):

```bash
sudo bash scripts/linux/install_all.sh
```

Editar `/etc/la_termalerp.env` y cambiar `DJANGO_SECRET_KEY`.

---

## Probar
- PC gerente: `http://IP_DEL_SERVIDOR:8000/dashboard/`
- Celular (Wi‑Fi): lo mismo

Si querés el acceso por nombre (ej. http://erp.local), después se agrega DNS local.
