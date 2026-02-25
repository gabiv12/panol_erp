# Pantalla TV Taller (Flota)

Esta pantalla existe para un caso operativo concreto:

- El taller NO usa celulares.
- Se instala una TV/pantalla grande donde se ve qué unidad requiere atención primero.
- El orden de prioridad se decide por la **próxima salida programada** (si existe).

## URL

`/flota/tv/taller/`

Querystring:
- `hours` (default 12): horizonte de salidas a considerar
- `refresh` (default 20): segundos de auto-recarga (meta refresh)
- `days` (default 30): antigüedad máxima de partes a incluir

Ejemplo:

`/flota/tv/taller/?hours=18&refresh=15&days=60`

## Regla de orden (importante)

1. Partes cuya unidad tiene salida dentro del rango `now..now+hours`:
   - ordenados por `salida_programada` más cercana
2. Partes sin salida en rango:
   - luego por severidad (Crítica > Alta > Media > Baja)
   - luego por recencia del parte

## Notas de implementación

- La pantalla está protegida por login y permiso `flota.view_partediario`.
- Para uso en TV, se recomienda iniciar sesión una vez con un usuario "kiosk" y dejar el navegador en pantalla completa.
- No modifica datos: es sólo lectura.
