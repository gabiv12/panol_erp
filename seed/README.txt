SEED (offline)

Comandos disponibles:

1) Exportar fixture JSON (seed):
   python manage.py export_seed --out seed/seed_export.json --apps flota inventario adjuntos

2) Importar fixture JSON:
   python manage.py import_seed --path seed/seed_export.json

3) Importar PARTES DIARIOS (Google Forms) desde XLSX:
   python manage.py import_partes_xlsx --path "C:\ruta\PARTES DIARIOS.xlsx"

4) Importar REGISTRO DE TALLER (Google Forms) desde XLSX:
   python manage.py import_taller_xlsx --path "C:\ruta\REGISTRO DE TALLER.xlsx"
