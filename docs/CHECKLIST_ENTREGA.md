# Checklist de entrega — Sprint Módulo A (Flota + Dashboard)

## Funcional
- [ ] Login operativo (acceso y redirecciones correctas).
- [ ] Dashboard visible autenticado.
- [ ] Dashboard muestra KPI + alertas VTV.
- [ ] Listado de colectivos muestra datos.
- [ ] Alta de colectivo funciona.
- [ ] Edición de colectivo funciona.
- [ ] Eliminación de colectivo funciona.
- [ ] Importar CSV funciona con archivo válido.
- [ ] Importar CSV muestra errores si hay duplicados/invalidaciones.
- [ ] Exportar CSV descarga correctamente.

## Seguridad
- [ ] Sin login: redirección a login.
- [ ] Usuario sin permiso `view_colectivo`: 403 en listado.
- [ ] Roles bootstrappeados correctamente con comando.

## UI/UX
- [ ] Modo claro/oscuro funciona y persiste.
- [ ] Responsive en móvil (tabla y formularios usables).
- [ ] Sin scroll innecesario en pantallas comunes (ajustes posteriores si hace falta).

## Offline
- [ ] Tailwind se genera local (sin CDN).
- [ ] Assets requeridos se sirven desde `/static`.
- [ ] Proyecto corre sin internet.

## Calidad
- [ ] `python manage.py test` pasa.
- [ ] Documentación presente en `/docs`.
