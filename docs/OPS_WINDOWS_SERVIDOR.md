# Operación Windows (Servidor local)

## Objetivo
Dejar La Termal ERP corriendo en una PC dedicada, accesible desde la LAN (PC gerente + celulares Wi‑Fi), con:
- arranque automático
- firewall restrictivo
- backups diarios
- logs
- (opcional) reportes programados

## 1) Ejecutar servidor manual (primera prueba)
En PowerShell (Administrador recomendado):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Run-Waitress.ps1 -ProjectRoot . -Host 0.0.0.0 -Port 8000 -LogDir .\logs
```

Requiere instalar `waitress`:
```powershell
python -m pip install waitress
```

## 2) Abrir firewall (LAN)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Firewall-ERP.ps1 -Port 8000 -Scope LocalSubnet
```

## 3) Instalar inicio automático
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Install-ServerTask.ps1 -ProjectRoot . -Host 0.0.0.0 -Port 8000 -LogDir .\logs
Start-ScheduledTask -TaskName "LaTermalERP-Server"
```

## 4) Backups diarios
Backup manual:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Backup-ERP.ps1 -ProjectRoot . -DataDir . -BackupDir .\backups -KeepDays 14
```

Instalar tarea diaria:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Install-BackupTask.ps1 -ProjectRoot . -DataDir . -BackupDir .\backups -KeepDays 14 -Hour 2 -Minute 0
```

## 5) Reportes programados (opcional)
Requiere el patch de reportes (comando `send_report_gerencia`).

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Install-ReportTask.ps1 -ProjectRoot . -Hour 7 -Minute 0 -Period daily -OutDir .\reportes
```

Eliminar tarea:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Uninstall-ReportTask.ps1
```
