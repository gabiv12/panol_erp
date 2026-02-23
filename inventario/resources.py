from import_export import resources, fields
from import_export.widgets import BooleanWidget, ForeignKeyWidget

from inventario.models import Producto, Categoria, Subcategoria, UnidadMedida, Proveedor


class ProductoResource(resources.ModelResource):
    codigo = fields.Field(attribute="codigo", column_name="codigo")
    nombre = fields.Field(attribute="nombre", column_name="nombre")
    descripcion = fields.Field(attribute="descripcion", column_name="descripcion")

    categoria = fields.Field(
        attribute="categoria",
        column_name="categoria",
        widget=ForeignKeyWidget(Categoria, "nombre"),
    )
    subcategoria = fields.Field(
        attribute="subcategoria",
        column_name="subcategoria",
        widget=ForeignKeyWidget(Subcategoria, "nombre"),
    )
    unidad_medida = fields.Field(
        attribute="unidad_medida",
        column_name="unidad_medida",
        widget=ForeignKeyWidget(UnidadMedida, "abreviatura"),
    )
    proveedor = fields.Field(
        attribute="proveedor",
        column_name="proveedor",
        widget=ForeignKeyWidget(Proveedor, "nombre"),
    )

    maneja_vencimiento = fields.Field(
        attribute="maneja_vencimiento",
        column_name="maneja_vencimiento",
        widget=BooleanWidget(),
    )
    is_active = fields.Field(
        attribute="is_active",
        column_name="is_active",
        widget=BooleanWidget(),
    )

    class Meta:
        model = Producto
        import_id_fields = ("codigo",)
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

        fields = (
            "codigo",
            "nombre",
            "descripcion",
            "categoria",
            "subcategoria",
            "unidad_medida",
            "proveedor",
            "stock_minimo",
            "maneja_vencimiento",
            "is_active",
        )
        export_order = fields

    def before_import_row(self, row, **kwargs):
        # Normalización básica
        if row.get("codigo") is not None:
            row["codigo"] = str(row["codigo"]).strip().upper()
        if row.get("nombre") is not None:
            row["nombre"] = str(row["nombre"]).strip()

        # FK: creación automática básica para carga inicial (Sprint 1)
        cat_name = (row.get("categoria") or "").strip()
        if cat_name:
            Categoria.objects.get_or_create(nombre=cat_name)

        prov_name = (row.get("proveedor") or "").strip()
        if prov_name:
            Proveedor.objects.get_or_create(nombre=prov_name)

        um_abbr = (row.get("unidad_medida") or "").strip()
        if um_abbr:
            UnidadMedida.objects.get_or_create(abreviatura=um_abbr, defaults={"nombre": um_abbr})

        # Subcategoría: si viene y existe categoría, crearla dentro de esa categoría
        sub_name = (row.get("subcategoria") or "").strip()
        if sub_name and cat_name:
            cat = Categoria.objects.filter(nombre=cat_name).first()
            if cat:
                Subcategoria.objects.get_or_create(categoria=cat, nombre=sub_name)
