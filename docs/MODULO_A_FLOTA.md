# Módulo A — Flota (Colectivos) + Dashboard (VTV)

## Objetivo
Implementar el primer módulo del ERP para carga y gestión de datos oficiales de colectivos, incluyendo:
- ABM de colectivos.
- Importación y exportación CSV.
- Dashboard inicial con alertas de VTV (vencidos / por vencer / sin fecha).
- Base preparada para crecer a inventario/taller.

## Alcance funcional
### Flota / Colectivos
- Listado con búsqueda.
- Alta / Edición / Baja (eliminación).
- Exportar CSV.
- Importar CSV (validación + vista de errores).

### Dashboard
- KPI: Colectivos activos.
- KPI: En taller (estado = TALLER).
- Alertas VTV:
  - Vencidos (fecha < hoy).
  - Por vencer (hoy <= fecha <= hoy + 30 días).
  - Sin fecha (revision_tecnica_vto null).

## Seguridad / Acceso
- El sistema requiere autenticación.
- Flota aplica control por permisos:
  - view_colectivo para ver listado.
  - add_colectivo / change_colectivo / delete_colectivo para ABM.
- Roles se bootstrappean con `python manage.py bootstrap_roles`.

## Datos y normalización
- `dominio` se normaliza a mayúsculas y sin espacios.
- `numero_chasis` se normaliza a mayúsculas y sin espacios.
- `interno`, `dominio`, `numero_chasis` son únicos.

## Estructura del proyecto
- `core`: dashboard, layout base, utilidades transversales.
- `usuarios`: login/logout (si corresponde) o integración con auth.
- `flota`: modelos, forms, filtros, import/export, vistas y templates.

Templates por app para escalabilidad:
- Cada app mantiene su propio `templates/<app>/...`.
- `templates/` global solo se usa para base/layout si se decide centralizar (opcional).

## Cómo correr en desarrollo
1) Activar venv.
2) Instalar dependencias.
3) Ejecutar:
- `npm run tw:build` (Tailwind local).
- `python manage.py migrate`
- `python manage.py runserver`

## Tailwind offline
- Tailwind se instala via `node_modules` local.
- El CSS se genera a `static/css/dist/styles.css`.
- No depende de CDN.

## Tests automatizados
- `core/tests.py`: dashboard (auth + conteos).
- `flota/tests.py`: permisos y accesos.

Ejecutar:
- `python manage.py test`
