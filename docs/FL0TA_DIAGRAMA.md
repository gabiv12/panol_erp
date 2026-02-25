# Flota – Horarios y Diagrama (interno)

Este documento explica el módulo de **Horarios** de La Termal ERP.

## Objetivo operativo
- Cargar salidas programadas y viajes especiales, tal cual se hace en planilla.
- Verlo en una pantalla tipo TV para taller/administración.
- Imprimir un "diagrama" del día.

## Flujo recomendado
1. A la tarde/noche (día anterior), ir a **Horarios** y elegir la fecha del día siguiente.
2. Cargar salidas (o usar **Copiar día anterior** y ajustar excepciones).
3. Abrir **Pantalla TV** para seguimiento.
4. Imprimir si hace falta.

## Componentes principales
- `SalidaProgramada` (modelo): representa una salida.
- `salidas_views.py`: CRUD, impresión, Pantalla TV y API mínima para alertas de partes.
- `salida_form.html`: wizard en 3 pasos para reducir errores.
- `seed_salidas_diagrama.py`: importación desde CSV para cargar rápido.

## API `api/colectivo-info/`
Devuelve alertas de partes abiertos por unidad. **No bloquea** la selección; solo avisa.

Campos:
- `partes.abiertos` = partes con estado ABIERTO o EN_PROCESO
- `partes.severidad_max` = severidad más alta abierta
- `partes.ultimo` = último parte abierto (resumen)

## Mantenimiento futuro
- Si más adelante se necesita "diagramas por patrón" (semanal), el modelo actual sirve como base.
- El wizard y la TV deben mantenerse simples (evitar lógica compleja en frontend).
