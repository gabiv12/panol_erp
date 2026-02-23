Guía rápida para ordenar el pañol (inventario físico)

1) Generar layout (ubicaciones) y pegar etiquetas
   python manage.py cargar_layout_ubicaciones --deposito DP --pasillos A,B --modulos 4 --niveles 4 --posiciones 4

   Esto crea códigos tipo:
     DP-A01-N01-P01
     DP-B04-N03-P02

   Pegá el CODIGO en la estantería/caja.

2) Cargar/ajustar stock real por ubicación
   - Si el producto está en el lugar correcto: podés usar un AJUSTE (delta) con referencia "TOMA".
   - Si está en otro lugar: usar TRANSFERENCIA (origen → destino).

3) Importación masiva (toma inicial)
   - Completa un CSV basado en stock_inicial_template.csv
   - Ejecuta:
     python manage.py importar_stock_inicial_csv --file inventario/demo/stock_inicial_template.csv --user demo

   El comando crea movimientos de AJUSTE para dejar el stock igual al CSV.

Recomendación de organización
- Agrupar por familias (filtros, correas, frenos, eléctrico, etc.).
- Reservar un pasillo/módulo para consumibles (precintos, cinta, fusibles, bulones).
- Crear ubicaciones separadas para "TALLER" (en uso) y "DEPÓSITO" (guardado).
