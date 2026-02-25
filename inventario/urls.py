from django.urls import path
from inventario import views

app_name = "inventario"

urlpatterns = [
    # Productos
    path("productos/", views.ProductoListView.as_view(), name="producto_list"),
    path("productos/nuevo/", views.ProductoCreateView.as_view(), name="producto_create"),
    path("productos/<int:pk>/editar/", views.ProductoUpdateView.as_view(), name="producto_update"),
    path("productos/<int:pk>/eliminar/", views.ProductoDeleteView.as_view(), name="producto_delete"),
    path("productos/<int:pk>/historial/", views.ProductoHistorialView.as_view(), name="producto_historial"),
    path("productos/importar/", views.productos_import_csv, name="producto_import"),
    path("productos/exportar/", views.productos_export_csv, name="producto_export"),

    # NUEVO: etiquetas PDF (respeta filtros por querystring)
    path("productos/etiquetas/", views.productos_etiquetas_pdf, name="producto_etiquetas"),

    # Stock
    path("stock/", views.StockActualListView.as_view(), name="stock_list"),

    # API (offline)
    path("api/stock-por-ubicacion/", views.stock_por_ubicacion_json, name="api_stock_por_ubicacion"),

    # Movimientos
    path("movimientos/", views.MovimientoStockListView.as_view(), name="movimiento_list"),
    path("movimientos/nuevo/", views.MovimientoStockCreateView.as_view(), name="movimiento_create"),
    path("movimientos/<int:pk>/editar/", views.MovimientoStockUpdateView.as_view(), name="movimiento_update"),
    path("movimientos/<int:pk>/eliminar/", views.MovimientoStockDeleteView.as_view(), name="movimiento_delete"),

    # Configuración (catálogos)
    path("categorias/", views.CategoriaListView.as_view(), name="categoria_list"),
    path("categorias/nuevo/", views.CategoriaCreateView.as_view(), name="categoria_create"),
    path("categorias/<int:pk>/editar/", views.CategoriaUpdateView.as_view(), name="categoria_update"),
    path("categorias/<int:pk>/eliminar/", views.CategoriaDeleteView.as_view(), name="categoria_delete"),

    path("subcategorias/", views.SubcategoriaListView.as_view(), name="subcategoria_list"),
    path("subcategorias/nuevo/", views.SubcategoriaCreateView.as_view(), name="subcategoria_create"),
    path("subcategorias/<int:pk>/editar/", views.SubcategoriaUpdateView.as_view(), name="subcategoria_update"),
    path("subcategorias/<int:pk>/eliminar/", views.SubcategoriaDeleteView.as_view(), name="subcategoria_delete"),

    path("unidades/", views.UnidadMedidaListView.as_view(), name="unidad_list"),
    path("unidades/nuevo/", views.UnidadMedidaCreateView.as_view(), name="unidad_create"),
    path("unidades/<int:pk>/editar/", views.UnidadMedidaUpdateView.as_view(), name="unidad_update"),
    path("unidades/<int:pk>/eliminar/", views.UnidadMedidaDeleteView.as_view(), name="unidad_delete"),

    path("ubicaciones/", views.UbicacionListView.as_view(), name="ubicacion_list"),
    path("ubicaciones/nuevo/", views.UbicacionCreateView.as_view(), name="ubicacion_create"),
    path("ubicaciones/<int:pk>/editar/", views.UbicacionUpdateView.as_view(), name="ubicacion_update"),
    path("ubicaciones/<int:pk>/eliminar/", views.UbicacionDeleteView.as_view(), name="ubicacion_delete"),

    path("proveedores/", views.ProveedorListView.as_view(), name="proveedor_list"),
    path("proveedores/nuevo/", views.ProveedorCreateView.as_view(), name="proveedor_create"),
    path("proveedores/<int:pk>/editar/", views.ProveedorUpdateView.as_view(), name="proveedor_update"),
    path("proveedores/<int:pk>/eliminar/", views.ProveedorDeleteView.as_view(), name="proveedor_delete"),
]