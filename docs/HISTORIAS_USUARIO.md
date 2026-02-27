# Historias de usuario — La Termal ERP / Pañol ERP

Este documento consolida las historias de usuario y criterios de aceptación del sistema **tal como está hoy** y del backlog inmediato.
Enfocado a operación real (offline-first, usuarios no técnicos) y cambios mínimos sin romper lo que funciona.

## 1) Roles (perfiles operativos)

- **Superusuario**: administra usuarios, roles y accesos por módulo. Acceso total.
- **Gerencia**: lectura amplia de operación (dashboards, listados, reportes). No carga operativa diaria (salvo excepción).
- **Diagramador / Supervisor**: gestiona flota (horarios, diagrama), choferes, unidades. Opera día a día.
- **Taller (mecánico)**: gestiona partes, priorización, TV Taller. Puede requerir lectura de horarios/diagrama para planificación.
- **Pañol**: inventario (productos, stock, movimientos) y apoyo a taller.
- **Cajero proveedores**: carga/edita datos de productos que ingresan (cuando se habilite el módulo de compras/proveedores).
- **Administración**: tareas administrativas sobre módulos habilitados (sin permisos de configuración global).
- **Chofer**: **solo** carga parte y (opcional) consulta de horario/diagrama (TV Horarios o vista restringida).

## 2) Principios no negociables (DoD)

- El sistema funciona **100% offline** (sin CDNs).
- UI consistente (ti-card/ti-input/ti-btn-*) y legible (personas grandes).
- Ningún flujo usa `alert()` / `confirm()` / modales del navegador: todo es UI interna.
- Errores 4xx/5xx tienen páginas amigables (en producción con DEBUG=False).
- Tests automatizados pasan (`python manage.py test`).
- Cambios mínimos; si se toca un módulo, no se rompe la navegación principal.

## 3) Módulo: Autenticación y sesión

### HU-AUTH-01 — Iniciar sesión
**Como** usuario habilitado  
**Quiero** iniciar sesión con usuario y contraseña  
**Para** acceder a los módulos según mi rol.

**Criterios de aceptación**
- Credenciales inválidas muestran mensaje claro en pantalla (sin romper layout).
- Redirección post-login a pantalla inicial operativa.
- Logout cierra sesión y vuelve al login.

### HU-AUTH-02 — Bloqueo por usuario inactivo
**Como** administración  
**Quiero** desactivar un usuario  
**Para** que no pueda iniciar sesión.

**Criterios**
- Usuario inactivo no puede loguearse (mensaje claro).
- No se eliminan registros históricos asociados.

## 4) Módulo: Usuarios y roles (accesos por módulo)

### HU-USR-01 — Alta/edición/baja de usuarios
**Como** superusuario  
**Quiero** crear/editar/eliminar usuarios  
**Para** administrar accesos del sistema.

**Criterios**
- Formularios validan campos obligatorios.
- Contraseña es opcional al editar (si no se completa, no cambia).
- Eliminar requiere confirmación **interna** (no del navegador).

### HU-USR-02 — Asignar rol y módulos visibles
**Como** superusuario  
**Quiero** asignar un rol y módulos habilitados por usuario  
**Para** que cada cuenta vea solo lo que necesita.

**Criterios**
- Solo superusuario ve la configuración de permisos.
- Sidebar y accesos se ajustan automáticamente.
- Los templates no realizan `user.has_perm()` directamente (se usa filter/tag o flags en contexto).

## 5) Módulo: Flota — Unidades

### HU-FLT-UNI-01 — Gestionar unidades
**Como** diagramador/supervisor  
**Quiero** crear/editar unidades (dominio, interno, estado, vencimientos)  
**Para** mantener la flota actualizada.

**Criterios**
- Listado con filtros básicos.
- Estado visible (activa/taller/baja).
- Adjuntos/fotos livianas (si aplica).

## 6) Módulo: Flota — Choferes

### HU-FLT-CHF-01 — Gestionar choferes
**Como** diagramador/supervisor  
**Quiero** alta/edición de chofer (legajo básico)  
**Para** asignar conductores en el diagrama.

**Criterios**
- Fotos opcionales y livianas.
- Búsqueda por apellido/nombre.
- Chofer inactivo no aparece en asignaciones.

## 7) Módulo: Flota — Horarios, salidas y diagrama

### HU-FLT-HOR-01 — Ver listado de salidas por fecha
**Como** diagramador  
**Quiero** ver las salidas de una fecha seleccionada  
**Para** operar el día.

**Criterios**
- Filtro por fecha y búsqueda por unidad/chofer/recorrido.
- “Hoy” y “Mañana” son accesos rápidos.
- La pantalla no cae con errores de rutas (NoReverseMatch).

### HU-FLT-HOR-02 — Horarios fijos + rotación de unidad/chofer
**Como** diagramador  
**Quiero** que los horarios base estén siempre disponibles  
**Para** rotar solo unidad/chofer y registrar excepciones.

**Criterios**
- Horarios base existen para el rango operativo (se generan/seed inicial).
- “Especial” se distingue visualmente (sin cambiar look&feel general).
- No se muestra texto redundante (“fijo”) si no aporta a operación.

### HU-FLT-HOR-03 — Viajes especiales multi‑día
**Como** diagramador  
**Quiero** cargar viajes especiales con rango de fechas  
**Para** que se mantengan visibles hasta el último día y afecten disponibilidad.

**Criterios**
- Especial aparece desde inicio hasta fin (inclusive).
- Al terminar el día de fin, ya no se muestra (fecha siguiente).

### HU-FLT-DIAG-01 — Editar diagrama (reemplazos rápidos)
**Como** diagramador  
**Quiero** editar rápidamente unidad y chofer del día  
**Para** reaccionar ante roturas/faltas de personal.

**Criterios**
- Edita solo unidad/chofer (sin modificar horarios base).
- Guarda cambios sin romper la tabla.
- Evita modales del navegador.

### HU-FLT-DIAG-02 — Vista doble (hoy + mañana)
**Como** diagramador  
**Quiero** ver el diagrama de hoy y mañana en paralelo  
**Para** decidir más rápido asignaciones y contingencias.

**Criterios**
- No requiere duplicar carga: solo comparación.
- Acceso desde Horarios.

## 8) Módulo: Pantallas TV

### HU-TV-HOR-01 — TV Horarios
**Como** chofer  
**Quiero** ver próximas salidas en una pantalla simple  
**Para** saber mi salida y regreso.

**Criterios**
- Tipografía grande, contraste fuerte, sin sidebar.
- Actualización periódica sin intervención.
- Puede fijarse a “hoy” o cambiar a “mañana” según decisión operativa (parametrizable).

### HU-TV-TLL-01 — TV Taller
**Como** taller/gerencia  
**Quiero** ver partes priorizados por próxima salida  
**Para** ordenar el trabajo.

**Criterios**
- Filtros por severidad/estado.
- Orden por prioridad (próxima salida dentro de ventana definida).

## 9) Módulo: Partes diarios (chofer)

### HU-PRT-01 — Cargar parte diario
**Como** chofer  
**Quiero** cargar un parte simple desde el celular  
**Para** reportar incidencias y checklist.

**Criterios**
- Solo pantallas de parte (sin admin extra).
- Adjuntar fotos/boletas de forma simple.
- No se eliminan partes (histórico); se puede “anular/corregir” según política.

## 10) Módulo: Inventario

### HU-INV-01 — Catálogo de productos
**Como** pañol  
**Quiero** listar/crear/editar productos  
**Para** tener control del stock.

### HU-INV-02 — Movimientos de stock
**Como** pañol  
**Quiero** registrar entradas/salidas/ajustes  
**Para** que el stock refleje lo real.

**Criterios**
- Motivo claro.
- Trazabilidad mínima (usuario/fecha).

## 11) Auditoría (backlog requerido)

### HU-AUD-01 — Historial de acciones por usuario
**Como** gerencia  
**Quiero** ver qué acciones realizó un usuario en un rango de fechas  
**Para** auditar operación (día/semana/mes).

**Criterios**
- Eventos mínimos: login/logout, CRUD salidas/diagrama, carga de partes, movimientos de inventario, cambios de usuarios/roles (solo superusuario).
- Filtro por usuario, módulo, rango de fechas.
- Exportable (CSV/PDF) cuando se habiliten reportes.

## 12) Integraciones (backlog)

### HU-INT-01 — Envío de reportes por email (gerencia)
**Como** sistema  
**Quiero** enviar un informe completo a gerencia  
**Para** seguimiento operativo.

### HU-INT-02 — Sincronización (Drive)
**Como** gerencia  
**Quiero** que reportes se suban a una carpeta controlada  
**Para** respaldar y compartir sin depender del servidor local.

---

## Apéndice A — Backlog de módulos futuros (alto nivel)

- Compras / Proveedores / Facturas
- Combustible (cargas y consumo)
- Órdenes de trabajo (taller)
- Repuestos / Consumos
- Alertas (vencimientos, stock bajo, roturas recurrentes)
- Reportes operativos y notificaciones
- Gomería (cubiertas)

