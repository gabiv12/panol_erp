@echo off
setlocal

REM ======================================================
REM La Termal ERP - Iniciar (modo LAN)
REM - Permite acceder desde otros dispositivos en la misma red
REM - Requiere que Windows Firewall permita el puerto 8000
REM - URL: http://IP_DE_ESTA_PC:8000/
REM ======================================================

cd /d "%~dp0"

if not exist "manage.py" (
  echo ERROR: No se encontro manage.py en %CD%
  echo Coloque este .bat dentro de la carpeta del proyecto.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
  echo ERROR: No se encontro el entorno virtual: .venv\Scripts\activate.bat
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

set PORT=8000

echo.
echo Servidor LAN iniciado.
echo Para entrar desde otro dispositivo: busque la IP de esta PC y use: http://IP:8000/
echo Para ver la IP: abra CMD y ejecute: ipconfig
echo.

python manage.py runserver 0.0.0.0:%PORT%

pause
