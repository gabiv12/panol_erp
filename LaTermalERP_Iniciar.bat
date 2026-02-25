@echo off
setlocal

REM ======================================================
REM La Termal ERP - Iniciar (modo local)
REM - Este archivo debe estar en la carpeta del proyecto (donde está manage.py)
REM - No requiere internet
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
  echo Verifique que existe la carpeta .venv dentro del proyecto.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

set PORT=8000

start "" "http://127.0.0.1:%PORT%/"

echo.
echo Servidor iniciado. NO cierre esta ventana mientras use el sistema.
echo Para cerrar: presione Ctrl + C y luego cierre esta ventana.
echo.

python manage.py runserver 127.0.0.1:%PORT%

pause
