Estado de entrega (local-first)

Objetivo inmediato:
- Operación diaria estable: Horarios, Diagrama, TV, Partes, Inventario.
- Roles operativos: CHOFERES, TALLER, DIAGRAMADOR, GERENCIA, ADMINISTRACION, CAJERO_PROVEEDORES.
- 100% offline: sin CDNs y con estáticos locales.

Manual de usuario:
- Ruta en el sistema: /manual/
- Archivo template: core/templates/core/manual_usuario.html
- Imágenes: static/manual/img/

Pruebas manuales:
- Ver docs/PLAN_PRUEBAS_MANUALES.md

Semillas / carga inicial:
- Export seed JSON: python manage.py export_seed --out seed/seed_export.json --apps flota inventario adjuntos
- Import seed JSON: python manage.py import_seed --path seed/seed_export.json

Limpiar datos de prueba:
- Borrar salidas por rango: python manage.py clear_salidas --from YYYY-MM-DD --to YYYY-MM-DD --yes
