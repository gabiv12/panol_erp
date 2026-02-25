# Flota – Diagrama (edición rápida) + alertas + TV

## Edición rápida del diagrama
Ruta:
- `/flota/salidas/diagrama/editar/?fecha=YYYY-MM-DD`

Uso:
- Para cambios de último momento (reemplazo de chofer, cambio de unidad, ajuste horario).
- Edita todo el día en una tabla.

Constancia:
- Cada modificación genera un registro en `django.contrib.admin.LogEntry` (sin migraciones adicionales).
- Se muestra “Historial de cambios” en la edición individual de una salida.

## Plan 15 días
- Botón “Editar diagrama” abre la edición rápida del día.
- La alerta “Revisar parte” linkea al parte abierto/en proceso de esa unidad.

## TV Taller
- Mejor contraste (fondo oscuro real).
- Leyenda de severidad y estado dentro de la pantalla.
- Botón “Pantalla completa” (requiere click por limitación del navegador).
- Parámetro `limit` para evitar scroll: `/flota/tv/taller/?limit=30`