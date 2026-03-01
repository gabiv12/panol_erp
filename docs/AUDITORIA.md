# Auditoría (historial de acciones)

Objetivo: que Gerencia/Superusuario pueda ver qué pantallas operó cada usuario, cuándo, y con qué resultado (status/duración). Esto sirve para control interno, soporte y trazabilidad.

## 1) Qué registra

Por cada request finalizado (GET/POST/PUT/PATCH/DELETE) de un usuario autenticado:

- Fecha/hora
- Usuario (username)
- Área (primer segmento de URL: flota / inventario / usuarios / ...)
- Acción (heurística): view / update / delete / login / logout
- Método + status HTTP
- Duración en ms
- Ruta (path)

No registra `/static/` ni `/media/`.

## 2) Acceso

- URL: `/auditoria/`
- Requiere permiso `auditoria.view_auditevent` o ser superusuario.

Filtros:

- Buscar: parte de la URL/vista/agente
- Usuario
- Área
- Acción
- Status
- Rango por fechas o “últimos N días”

## 3) Exportar a CSV

En la pantalla de Auditoría, usá **Exportar CSV**. Exporta lo mismo que estás filtrando en pantalla.

- Formato: UTF-8 con BOM (abre bien en Excel en Windows).
- Límite de seguridad: 50.000 filas por export.
