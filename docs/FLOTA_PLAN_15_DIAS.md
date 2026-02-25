# Plan 15 días (Flota)

## Objetivo operativo
Permitir al diagramador armar una planificación quincenal (15 días) y luego ajustar excepciones.

## Qué resuelve
- Turnos rotativos: suelen cambiar cada 15 días.
- Reduce el trabajo repetido cuando la mayoría de salidas se mantienen.

## Flujos
### 1) Horarios (día puntual)
- Cargar y corregir un día específico.
- Botones:
  - Copiar día anterior
  - Copiar 15 días (replica el día seleccionado hacia adelante)

### 2) Plan 15 días
- Vista agenda (15 días desde una fecha).
- Acciones:
  - Abrir el día en Horarios para editar
  - Imprimir
  - Exportar CSV

## Reglas de duplicados al copiar
Se evita duplicar por: (colectivo_id + salida_programada exacta) dentro del rango.
