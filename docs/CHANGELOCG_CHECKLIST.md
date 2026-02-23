# Checklist de entrega (cada actualización)

1) Código
- [ ] Cambios commiteados en Git
- [ ] No hay archivos .bak/.tmp dentro del repo (o están en _trash/)
- [ ] No se tocaron migraciones antiguas de inventario (solo safe/hotfix)

2) Base de datos / Migraciones
- [ ] python manage.py check
- [ ] python manage.py showmigrations inventario
- [ ] Navegación principal sin errores (dashboard, flota, inventario)

3) Pruebas manuales mínimas
- [ ] Login OK
- [ ] /dashboard/ OK
- [ ] /flota/colectivos/ OK
- [ ] Informe 30 días por unidad OK
- [ ] /inventario/productos/ OK
- [ ] /inventario/stock/ OK (low=1)
- [ ] /inventario/movimientos/ OK
- [ ] Crear movimiento OK (ingreso y egreso)
- [ ] Editar movimiento OK
- [ ] Eliminar movimiento OK

4) Documentación
- [ ] Actualizar docs/OPERATIVA.docx si cambió el proceso
- [ ] Actualizar docs/CHANGELOG.md
- [ ] Si cambió un CSV, actualizar la plantilla en docs/plantillas_csv/