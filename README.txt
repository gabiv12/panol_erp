Aplicación (PowerShell):

Set-Location "C:\Users\gabi\Desktop\2026\panol_erp"
.\.venv\Scripts\Activate.ps1

# Extraé el zip arriba del proyecto (mantiene /scripts)
powershell -ExecutionPolicy Bypass -File .\scripts\apply_hotfix.ps1 -ProjectRoot (Get-Location).Path

Luego:
npm run tw:build
python manage.py test

Prueba:
- Abrí el sitio en modo móvil y tocá el botón Menú (debe abrir/cerrar el drawer)
- Probá crear una Entrada (Ingreso) y luego un Egreso: el mensaje de stock ahora guía mejor.
