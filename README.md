# La Termal

Sistema local-first (offline) orientado a la gestiÃ³n operativa de una empresa de transporte.

Estado actual:
- MÃ³dulos operativos: Inventario + Flota + Adjuntos
- Tailwind local (offline)

## Requisitos
- Python 3.12+
- Node.js (para Tailwind)
- Entorno virtual Python (recomendado)

## InstalaciÃ³n (local)
1) Crear y activar entorno virtual
2) Instalar dependencias Python
3) Instalar dependencias Node
4) Construir Tailwind
5) Migrar base
6) Crear superusuario
7) Levantar servidor

## Comandos (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
npm install

npm run tw:build

python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
```

## Migraciones en DB nueva vs DB existente

Si estÃ¡s trabajando con una base de datos ya usada (donde se aplicÃ³ `--fake` para alinear), revisÃ¡:
- `docs/MIGRACIONES.md`
