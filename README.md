# Pañol ERP

Sistema local-first (offline) orientado a la gestión operativa de una empresa de transporte.
Sprint 1: Módulo Flota + Dashboard de alertas VTV (30 días).

## Requisitos
- Python 3.12+
- Node.js (para Tailwind)
- Entorno virtual Python (recomendado)

## Instalación (local)
1. Crear y activar entorno virtual
2. Instalar dependencias Python
3. Instalar dependencias Node
4. Construir Tailwind
5. Migrar base
6. Crear superusuario
7. Crear roles base

## Comandos (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
npm install

npm run tw:build

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

python manage.py bootstrap_roles

python manage.py runserver
