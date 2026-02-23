# Tests manuales — Módulo A (Flota + Dashboard)

## Convenciones
- ID: TM-FLOTA-XX
- Severidad: Baja / Media / Alta
- Resultado esperado: describir con precisión.

---

## TM-FLOTA-01 — Acceso sin autenticación redirige a login
Precondición: usuario no autenticado.  
Pasos:
1. Ir a `/`.
Resultado esperado:
- Redirige a `/login/`.
Severidad: Alta

## TM-FLOTA-02 — Acceso dashboard autenticado
Precondición: usuario autenticado.  
Pasos:
1. Ir a `/`.
Resultado esperado:
- Responde 200.
- Se ven KPIs y secciones de VTV.
Severidad: Alta

## TM-FLOTA-03 — Usuario sin permiso no puede ver lista
Precondición: usuario autenticado sin `view_colectivo`.  
Pasos:
1. Ir a `/flota/colectivos/`.
Resultado esperado:
- Responde 403.
Severidad: Alta

## TM-FLOTA-04 — Usuario con permiso puede ver lista
Precondición: usuario autenticado con `view_colectivo`.  
Pasos:
1. Ir a `/flota/colectivos/`.
Resultado esperado:
- Responde 200.
- Se ve tabla con registros.
Severidad: Alta

## TM-FLOTA-05 — Alta de colectivo válida
Precondición: usuario con `add_colectivo`.  
Pasos:
1. Ir a “Nuevo”.
2. Completar interno, dominio, año, marca, modelo, chasis.
3. Guardar.
Resultado esperado:
- Redirige a listado.
- Registro aparece en tabla.
Severidad: Alta

## TM-FLOTA-06 — Validación de unicidad interno
Precondición: existe un colectivo con interno X.  
Pasos:
1. Crear otro con mismo interno X.
Resultado esperado:
- Error de validación por duplicado.
Severidad: Alta

## TM-FLOTA-07 — Importar CSV válido
Precondición: usuario con permisos de importación (si aplica en vista).  
Pasos:
1. Ir a Importar CSV.
2. Seleccionar CSV válido.
3. Confirmar.
Resultado esperado:
- Mensaje de éxito.
- Registros cargados/actualizados según estrategia.
Severidad: Alta

## TM-FLOTA-08 — Importar CSV con duplicados
Precondición: ya existen registros con mismo chasis/dominio/interno.  
Pasos:
1. Importar CSV duplicado.
Resultado esperado:
- Se muestran errores por fila.
- No se importa parcialmente (o se define política).
Severidad: Alta

## TM-FLOTA-09 — Exportar CSV
Pasos:
1. Ir a Exportar CSV.
Resultado esperado:
- Descarga archivo CSV.
- Contenido coincide con registros del listado.
Severidad: Media

## TM-FLOTA-10 — Dashboard: VTV sin fecha
Precondición: existen colectivos con revision_tecnica_vto = null.  
Pasos:
1. Abrir dashboard.
Resultado esperado:
- KPI “VTV sin fecha” coincide con cantidad real.
- Se listan unidades (hasta límite).
Severidad: Media

## TM-FLOTA-11 — Dashboard: VTV vencidos
Precondición: existe colectivo con vto < hoy.  
Pasos:
1. Abrir dashboard.
Resultado esperado:
- Aparece en “VTV vencidos”.
Severidad: Alta

## TM-FLOTA-12 — Dashboard: VTV por vencer (30 días)
Precondición: existe colectivo con vto dentro de 30 días.  
Pasos:
1. Abrir dashboard.
Resultado esperado:
- Aparece en “VTV por vencer”.
Severidad: Alta
