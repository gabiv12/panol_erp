# Checklist de entrega a producción local (LAN / Offline)

## 1) Configuración básica
- Verificar `DEBUG=False` en entorno de producción (no en desarrollo).
- Configurar `ALLOWED_HOSTS` con IP/host de la LAN.
- Mantener estáticos locales (sin CDNs).

## 2) Base de datos
- Backup de la base antes de cambios.
- Migraciones aplicadas (`python manage.py migrate`).
- Seed de horarios fijos para rango operativo (si corresponde).

## 3) Pruebas mínimas (smoke)
- Login/logout.
- Sidebar: navegación por módulos permitidos.
- Flota: Unidades / Choferes / Horarios / Diagrama / TV.
- Partes: listar y cargar uno.
- Inventario: listar productos y movimientos.

## 4) Errores 404/500
- En desarrollo con `DEBUG=True` Django muestra pantalla de debug.
- Para verificar páginas 404/500 personalizadas: ejecutar con `DEBUG=False` y provocar un 404/500 controlado.

## Auditoría (Gerencia)

- `python manage.py migrate`
- `python manage.py init_auditoria`
- Verificar acceso: `/auditoria/`

