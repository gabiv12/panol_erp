# Accesos y roles

Este sistema está pensado para operación real. Para mantener simple el uso y evitar que cada usuario vea opciones que no necesita, se usan **roles**.

## Cómo funciona

- Un **rol** se implementa como un **Grupo** de Django.
- Cada grupo tiene un set de **permisos** (view/add/change/delete) por módulo.
- El menú lateral se adapta según los permisos (y/o flags del sistema).

## Inicializar roles

Ejecutar una sola vez (o cuando actualicemos roles):

```powershell
python manage.py init_roles
```

Esto crea/actualiza los grupos:

- GERENCIA (acceso total)
- DIAGRAMADOR
- TALLER
- CHOFERES
- PANOL
- ADMINISTRACION

## Asignar rol a un usuario

1. Ir a **Sistema → Administración → Nuevo usuario**.
2. Completar usuario y contraseña.
3. Elegir **Rol**.
4. Guardar.

> Nota: si cambiás el rol, el sistema reemplaza el grupo anterior (1 rol principal por usuario).

## Recomendación de perfiles

- **Gerencia**: ve todo.
- **Diagramación / Coordinación**: Horarios/Diagrama + Choferes + consulta de partes/unidades.
- **Taller**: Partes diarios (gestión) + consulta de unidades.
- **Chofer**: carga de parte (desde celular) + consulta mínima.
- **Pañol / Inventario**: Inventario + Movimientos.
- **Administración**: lectura de inventario/flota, y a futuro compras/combustible/reportes.
