# Roles y permisos (La Termal ERP)

El sistema usa **Grupos de Django** como roles. Cada usuario puede tener **un rol principal** (por ahora).

## Roles disponibles

- **Gerencia / Administrador** (`ADMIN`)
  - Acceso total (Flota + Inventario + Usuarios).
- **Diagramador / Supervisor** (`SUPERVISOR`)
  - Flota completa (unidades, horarios/diagrama, partes) y gestión de choferes.
  - Puede crear/editar usuarios.
- **Pañol / Inventario** (`PANOLERO`)
  - Productos, stock y movimientos.
- **Taller** (`MECANICO`)
  - Partes diarios (ver/gestionar) y pantallas TV de taller.
- **Chofer** (`CHOFER`)
  - Carga de parte desde celular y lectura de horarios/diagrama.

## Cómo asignar un rol

1. Ingresá con un usuario **Gerencia/Administrador** o **Diagramador/Supervisor**.
2. Ir a **Administración → Usuarios y roles**.
3. Crear o editar un usuario y elegir el **Rol**.
4. Guardar.

## Nota sobre permisos

Los menús se ocultan si el usuario no tiene permisos del módulo, para evitar pantallas **403**.

Si querés permitir combinaciones de roles (ej. Inventario + Taller), se puede cambiar a multi-rol.
