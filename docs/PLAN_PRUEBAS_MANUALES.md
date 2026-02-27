Plan de pruebas manuales (operativo)

Regla: ejecutar con al menos 2 perfiles
- Superusuario (administración total)
- Chofer (rol CHOFERES)
- (Opcional) Taller

Precondición:
- python manage.py check (0 issues)
- python manage.py test (OK)

1) Login / Logout
- Abrir /login/
- Probar credenciales correctas
- Probar credenciales incorrectas (debe mostrar "Usuario o contraseña inválidos")
- Logout (POST /logout/) y volver a /login/

2) Sidebar / Navegación
- En super: ver Flota, Inventario, Usuarios, TV, Manual
- En chofer: ver solo "Cargar parte" + "Horarios TV" + "Manual" (según configuración)

3) Flota > Unidades
- Listado: interno + dominio visibles
- Alta: crear unidad mínima
- Editar: guardar cambios
- Eliminar: confirmación interna (no confirm del navegador)

4) Flota > Horarios
- Abrir /flota/salidas/
- Cambiar fecha y filtrar
- Nueva salida (wizard): guardar
- Imprimir diagrama: abre en nueva pestaña
- Editar diagrama (bulk): guardar y ver historial

5) Horarios (doble)
- Abrir /flota/salidas/doble/?fecha=YYYY-MM-DD
- Ver tablas Día A y Día B

6) TV Horarios
- Super: /flota/tv/horarios/ debe mostrar "Diagrama: dd/mm/aaaa"
- Chofer: debe acceder (si se habilitó) y ver el mismo contenido

7) TV Taller
- /flota/tv/taller/ debe listar partes con severidad/estado, y refrescar parcial si corresponde

8) Partes diarios
- Listado: filtros básicos
- Crear parte (operador)
- Crear parte chofer (celular)

9) Inventario
- Productos: filtro y detalle
- Movimientos: crear ingreso/egreso y verificar stock

Criterio de aceptación:
- No hay errores 500
- No hay confirm/alert del navegador en acciones operativas
- TV Horarios no queda vacía si existe un día con salidas (fallback al último día con datos)
