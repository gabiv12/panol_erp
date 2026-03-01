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

## 10) Módulo: Inventario (ampliación operativa + ubicaciones físicas)

### HU-INV-04 — Ubicaciones físicas jerárquicas (Depósito/Pasillo/Módulo/Nivel/Posición)
Como **encargado de Pañol**  
Quiero **definir ubicaciones físicas reales** (depósito, pasillo, módulo, nivel, posición)  
Para **encontrar repuestos rápido y sin dudas**, y que cualquier persona pueda ubicar un ítem.

**Criterios de aceptación**
- Se pueden crear ubicaciones con un **código único** (ej: `DP-A-M02-N03-P01`).
- Se puede armar un **layout** (estructura completa) para un depósito con pasillos/módulos/niveles/posiciones.
- Se puede **exportar a CSV** la lista de ubicaciones.
- Se puede **importar/actualizar por CSV** (sin romper códigos existentes).
- En la UI se puede **buscar** por código o nombre y ver el “camino” (depósito → pasillo → …).

---

### HU-INV-05 — Ordenar el depósito en el sistema y luego acomodar físicamente
Como **encargado de Pañol**  
Quiero **cargar primero el orden “ideal” en el sistema**  
Para luego **acomodar físicamente el depósito** siguiendo esa estructura y que el sistema guíe el reordenamiento.

**Criterios de aceptación**
- Puedo crear ubicaciones antes de mover físicamente nada.
- Puedo listar “ubicaciones vacías” y “ubicaciones con stock”.
- Puedo registrar reubicaciones para ir pasando productos a su lugar final.

---

### HU-INV-06 — Carga inicial de stock (arranque) por CSV
Como **encargado de Pañol**  
Quiero **cargar el stock inicial por CSV**  
Para **poner el sistema en marcha** sin tener que cargar movimiento por movimiento.

**Criterios de aceptación**
- El CSV permite: producto, ubicación, cantidad.
- Valida que existan producto y ubicación.
- Permite “dry-run” (simulación) antes de aplicar.
- Al aplicar, deja `StockActual` consistente y registra auditoría/movimiento de tipo ajuste inicial si corresponde (según decisión de implementación).

---

### HU-INV-07 — Reubicaciones/Transferencias (incluye masivo por CSV)
Como **encargado de Pañol**  
Quiero **mover stock entre ubicaciones** (transferencias)  
Para reflejar **reordenamientos** y también movimientos internos del depósito.

**Criterios de aceptación**
- Transferencia descuenta de origen y suma en destino en una sola operación.
- Si no hay stock suficiente en origen, bloquea o informa error.
- Soporta CSV para reubicaciones masivas (ej: “pasar todo el pasillo A al pasillo B”).
- Registra quién hizo la operación y una referencia/observación.

---

### HU-INV-08 — Cantidades enteras vs decimales según unidad de medida
Como **usuario de Inventario**  
Quiero que el sistema **muestre y valide cantidades** según la unidad (entera o decimal)  
Para evitar errores (ej: “2.500 unidades” no tiene sentido si la unidad es “unidad”, pero sí si es “litro/kg”).

**Criterios de aceptación**
- Si `UnidadMedida.permite_decimales = False`, el sistema obliga cantidades enteras (o redondea según reglas definidas).
- Si permite decimales, muestra con 3 decimales o el formato definido.
- En listados y formularios, el usuario entiende claramente el formato.

---

### HU-INV-09 — Flujo operativo: Solicitud/Entrega/Consumo (Pañol ↔ Mecánico)
Como **mecánico**  
Quiero **solicitar repuestos** indicando unidad (colectivo) y motivo  
Para que **Pañol entregue** lo necesario y quede trazabilidad.

Como **encargado de Pañol**  
Quiero **registrar la entrega/egreso** contra una solicitud  
Para descontar stock y dejar registro del responsable.

**Criterios de aceptación**
- La solicitud se vincula a: colectivo (interno), parte/tarea (si aplica), y lista de repuestos.
- La entrega genera movimientos de egreso y deja evidencia (quién entregó / quién recibió).
- Se puede ver historial por colectivo: partes → repuestos consumidos → movimientos.

---

### HU-INV-10 — Integración con Partes Diarios (Chofer → Tarea → Repuestos → Stock)
Como **chofer**  
Quiero cargar un **parte diario** del colectivo (problema, severidad, fecha)  
Para que Taller/Mecánica tenga tareas claras.

Como **mecánico/encargado**  
Quiero vincular ese parte con **repuestos usados**  
Para tener trazabilidad completa (incidencia → solución → costo/consumo).

**Criterios de aceptación**
- Un parte diario se asocia a un colectivo (interno) y puede pasar a “tarea”.
- Se pueden asociar repuestos sugeridos/usados.
- Reportes: repuestos más consumidos por tipo de incidencia/colectivo.

---

## 14) Módulo: Gomería / Neumáticos (nuevo módulo propuesto)

### HU-GOM-01 — Alta de neumático/cubierta con identificación interna
Como **gomero/encargado**  
Quiero registrar una cubierta con un **número interno**  
Para identificarla siempre aunque cambie de vehículo.

**Datos típicos**
- Número interno de cubierta
- Medida, marca, modelo
- Estado: NUEVA / RECAPADA
- Proveedor, costo, fecha de alta
- Ubicación física (depósito/posición)

---

### HU-GOM-02 — Montaje/Desmontaje en colectivo y posición
Como **gomero/encargado**  
Quiero registrar cuando una cubierta se monta o desmonta de un colectivo y en qué posición  
Para llevar historial completo y saber dónde está cada cubierta.

**Criterios de aceptación**
- Se registra: colectivo (interno), posición (ej: delantera izq), fecha, km (si se dispone), motivo.
- La cubierta queda “asignada” al colectivo mientras esté montada.

---

### HU-GOM-03 — Vida útil y alertas (km/días)
Como **encargado**  
Quiero medir vida útil de cubiertas  
Para anticipar recambio/recap y reducir costos por fallas.

**Criterios de aceptación**
- Cálculo de duración por km o por días (según datos disponibles).
- Alertas por vencimiento de vida útil o por cantidad de recapados.

---

### HU-GOM-04 — Relación con Inventario (stock + activos serializados)
Como **encargado**  
Quiero que el sistema maneje cubiertas como **activos individualizados** (serializados) y también como stock de repuesto  
Para controlar tanto “la cubierta puntual” como el “inventario disponible”.

**Criterios de aceptación**
- Una cubierta individual puede tener ubicación física (igual que un repuesto).
- Movimientos: ingreso compra, transferencia de ubicación, montaje (sale de depósito a unidad), desmontaje (vuelve), baja.

---

## 15) Operación / Demo remota (ngrok)

### HU-OPS-01 — Exponer demo por ngrok sin romper login (CSRF)
Como **responsable del sistema**  
Quiero compartir una demo por ngrok para mostrar avances  
Para que terceros puedan ver el módulo sin estar en la red local.

**Criterios de aceptación**
- El login funciona por HTTPS detrás de proxy (ngrok) sin error CSRF.
- Configuración documentada: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, cabecera `SECURE_PROXY_SSL_HEADER`, y configuración de cookies si aplica.
- Opción de “modo demo” con usuario de prueba y permisos mínimos.

---

## 16) Arquitectura / Base de datos (decisión documentada)

### HU-ARCH-01 — Dev con SQLite y producción con MariaDB (plan de cambio)
Como **responsable técnico**  
Quiero mantener SQLite para desarrollo rápido y pasar a MariaDB en producción  
Para soportar mejor operación real sin frenar el avance del proyecto.

**Criterios de aceptación**
- Settings por variables de entorno para elegir motor de BD.
- Procedimiento documentado para migrar y validar datos.
- Momento recomendado para el cambio: cuando Inventario + Flota + Taller estén estables y testeados.