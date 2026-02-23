from __future__ import annotations

from io import BytesIO

from tablib import Dataset

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

# ReportLab (opcional): si falta, el sistema igual levanta y solo falla el endpoint de etiquetas
try:
    from reportlab.graphics.barcode import code128
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    REPORTLAB_OK = True
except Exception:
    code128 = None
    A4 = None
    mm = None
    canvas = None
    REPORTLAB_OK = False

from flota.models import Colectivo

from adjuntos.forms import ProductoImagenInlineFormSet

from inventario.filters import ProductoFilter, StockActualFilter, MovimientoStockFilter
from inventario.forms import (
    CategoriaForm,
    SubcategoriaForm,
    UnidadMedidaForm,
    UbicacionForm,
    ProveedorForm,
    ProductoForm,
    MovimientoStockForm,
)
from inventario.models import (
    Categoria,
    Subcategoria,
    UnidadMedida,
    Ubicacion,
    Proveedor,
    Producto,
    StockActual,
    MovimientoStock,
)
from inventario.resources import ProductoResource
from inventario.services import stock as stock_service

# -----------------------------
# Helpers base (católogos simples)
# -----------------------------
class SimpleContextMixin:
    title = ""
    subtitle = ""
    active_tab = "config"

    create_url_name = ""
    update_url_name = ""
    delete_url_name = ""
    list_url_name = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.title
        ctx["subtitle"] = self.subtitle
        ctx["active_tab"] = self.active_tab
        ctx["create_url_name"] = self.create_url_name
        ctx["update_url_name"] = self.update_url_name
        ctx["delete_url_name"] = self.delete_url_name
        ctx["list_url_name"] = self.list_url_name
        return ctx


class SimpleListView(LoginRequiredMixin, PermissionRequiredMixin, SimpleContextMixin, ListView):
    template_name = "inventario/simple_list.html"
    paginate_by = 20


class SimpleCreateView(LoginRequiredMixin, PermissionRequiredMixin, SimpleContextMixin, CreateView):
    template_name = "inventario/simple_form.html"

    def get_success_url(self):
        return reverse(self.list_url_name or self.success_url_name)


class SimpleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SimpleContextMixin, UpdateView):
    template_name = "inventario/simple_form.html"

    def get_success_url(self):
        return reverse(self.list_url_name or self.success_url_name)


class SimpleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SimpleContextMixin, DeleteView):
    template_name = "inventario/simple_confirm_delete.html"

    def get_success_url(self):
        return reverse(self.list_url_name or self.success_url_name)


# -----------------------------
# Categorï¿½as
# -----------------------------
class CategoriaListView(SimpleListView):
    model = Categoria
    permission_required = "inventario.view_categoria"
    title = "Categorías"
    subtitle = "Clasificación principal de productos."
    active_tab = "config"
    create_url_name = "inventario:categoria_create"
    update_url_name = "inventario:categoria_update"
    delete_url_name = "inventario:categoria_delete"
    list_url_name = "inventario:categoria_list"


class CategoriaCreateView(SimpleCreateView):
    model = Categoria
    form_class = CategoriaForm
    permission_required = "inventario.add_categoria"
    title = "Nueva categoría"
    subtitle = "Crear una categoría de inventario."
    active_tab = "config"
    list_url_name = "inventario:categoria_list"


class CategoriaUpdateView(SimpleUpdateView):
    model = Categoria
    form_class = CategoriaForm
    permission_required = "inventario.change_categoria"
    title = "Editar categoría"
    subtitle = "Actualizar datos de la categoría."
    active_tab = "config"
    list_url_name = "inventario:categoria_list"


class CategoriaDeleteView(SimpleDeleteView):
    model = Categoria
    permission_required = "inventario.delete_categoria"
    title = "Eliminar categoría"
    subtitle = "Acción irreversible."
    active_tab = "config"
    list_url_name = "inventario:categoria_list"


# -----------------------------
# Subcategoróas
# -----------------------------
class SubcategoriaListView(SimpleListView):
    model = Subcategoria
    permission_required = "inventario.view_subcategoria"
    title = "Subcategoróas"
    subtitle = "Clasificaciï¿½n secundaria dentro de una categoría."
    active_tab = "config"
    create_url_name = "inventario:subcategoria_create"
    update_url_name = "inventario:subcategoria_update"
    delete_url_name = "inventario:subcategoria_delete"
    list_url_name = "inventario:subcategoria_list"


class SubcategoriaCreateView(SimpleCreateView):
    model = Subcategoria
    form_class = SubcategoriaForm
    permission_required = "inventario.add_subcategoria"
    title = "Nueva subcategoría"
    subtitle = "Crear una subcategoría asociadaía una categoría."
    active_tab = "config"
    list_url_name = "inventario:subcategoria_list"


class SubcategoriaUpdateView(SimpleUpdateView):
    model = Subcategoria
    form_class = SubcategoriaForm
    permission_required = "inventario.change_subcategoria"
    title = "Editar subcategoría"
    subtitle = "Actualizar datos de la subcategoría."
    active_tab = "config"
    list_url_name = "inventario:subcategoria_list"


class SubcategoriaDeleteView(SimpleDeleteView):
    model = Subcategoria
    permission_required = "inventario.delete_subcategoria"
    title = "Eliminar subcategoría"
    subtitle = "Acción irreversible."
    active_tab = "config"
    list_url_name = "inventario:subcategoria_list"


# -----------------------------
# Unidades
# -----------------------------
class UnidadMedidaListView(SimpleListView):
    model = UnidadMedida
    permission_required = "inventario.view_unidadmedida"
    title = "Unidades de medida"
    subtitle = "Define cómo se mide el stock (unidad, kg, litro, etc.)."
    active_tab = "config"
    create_url_name = "inventario:unidad_create"
    update_url_name = "inventario:unidad_update"
    delete_url_name = "inventario:unidad_delete"
    list_url_name = "inventario:unidad_list"


class UnidadMedidaCreateView(SimpleCreateView):
    model = UnidadMedida
    form_class = UnidadMedidaForm
    permission_required = "inventario.add_unidadmedida"
    title = "Nueva unidad"
    subtitle = "Crear unidad de medida."
    active_tab = "config"
    list_url_name = "inventario:unidad_list"


class UnidadMedidaUpdateView(SimpleUpdateView):
    model = UnidadMedida
    form_class = UnidadMedidaForm
    permission_required = "inventario.change_unidadmedida"
    title = "Editar unidad"
    subtitle = "Actualizar unidad de medida."
    active_tab = "config"
    list_url_name = "inventario:unidad_list"


class UnidadMedidaDeleteView(SimpleDeleteView):
    model = UnidadMedida
    permission_required = "inventario.delete_unidadmedida"
    title = "Eliminar unidad"
    subtitle = "Acción irreversible."
    active_tab = "config"
    list_url_name = "inventario:unidad_list"


# -----------------------------
# Ubicaciones
# -----------------------------
class UbicacionListView(SimpleListView):
    model = Ubicacion
    permission_required = "inventario.view_ubicacion"
    title = "Ubicaciones"
    subtitle = "Estanterías, depósitos y zonas de almacenamiento."
    active_tab = "config"
    create_url_name = "inventario:ubicacion_create"
    update_url_name = "inventario:ubicacion_update"
    delete_url_name = "inventario:ubicacion_delete"
    list_url_name = "inventario:ubicacion_list"


class UbicacionCreateView(SimpleCreateView):
    model = Ubicacion
    form_class = UbicacionForm
    permission_required = "inventario.add_ubicacion"
    title = "Nueva ubicación"
    subtitle = "Crear ubicación fósica de almacenamiento."
    active_tab = "config"
    list_url_name = "inventario:ubicacion_list"


class UbicacionUpdateView(SimpleUpdateView):
    model = Ubicacion
    form_class = UbicacionForm
    permission_required = "inventario.change_ubicacion"
    title = "Editar ubicación"
    subtitle = "Actualizar ubicación."
    active_tab = "config"
    list_url_name = "inventario:ubicacion_list"


class UbicacionDeleteView(SimpleDeleteView):
    model = Ubicacion
    permission_required = "inventario.delete_ubicacion"
    title = "Eliminar ubicación"
    subtitle = "Acción irreversible."
    active_tab = "config"
    list_url_name = "inventario:ubicacion_list"


# -----------------------------
# Proveedores
# -----------------------------
class ProveedorListView(SimpleListView):
    model = Proveedor
    permission_required = "inventario.view_proveedor"
    title = "Proveedores"
    subtitle = "Datos bósicos de proveedores."
    active_tab = "config"
    create_url_name = "inventario:proveedor_create"
    update_url_name = "inventario:proveedor_update"
    delete_url_name = "inventario:proveedor_delete"
    list_url_name = "inventario:proveedor_list"


class ProveedorCreateView(SimpleCreateView):
    model = Proveedor
    form_class = ProveedorForm
    permission_required = "inventario.add_proveedor"
    title = "Nuevo proveedor"
    subtitle = "Crear proveedor."
    active_tab = "config"
    list_url_name = "inventario:proveedor_list"


class ProveedorUpdateView(SimpleUpdateView):
    model = Proveedor
    form_class = ProveedorForm
    permission_required = "inventario.change_proveedor"
    title = "Editar proveedor"
    subtitle = "Actualizar proveedor."
    active_tab = "config"
    list_url_name = "inventario:proveedor_list"


class ProveedorDeleteView(SimpleDeleteView):
    model = Proveedor
    permission_required = "inventario.delete_proveedor"
    title = "Eliminar proveedor"
    subtitle = "Acción irreversible."
    active_tab = "config"
    list_url_name = "inventario:proveedor_list"


# -----------------------------
# Productos
# -----------------------------
class ProductoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Producto
    template_name = "inventario/producto_list.html"
    paginate_by = 20
    permission_required = "inventario.view_producto"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("categoria", "subcategoria", "unidad_medida", "proveedor")
            .prefetch_related("imagenes")  # para miniatura sin N+1
        )
        qs = qs.annotate(stock_total=Sum("stocks__cantidad"))
        self.filterset = ProductoFilter(self.request.GET, queryset=qs)
        return self.filterset.qs.order_by("codigo")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filterset"] = self.filterset
        ctx["active_tab"] = "productos"
        return ctx


class ProductoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "inventario/producto_form.html"
    permission_required = "inventario.add_producto"

    def get_success_url(self):
        return reverse("inventario:producto_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = "productos"
        if "imagenes_formset" not in ctx:
            ctx["imagenes_formset"] = ProductoImagenInlineFormSet(instance=getattr(self, "object", None) or Producto())
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = ProductoImagenInlineFormSet(self.request.POST, self.request.FILES, instance=form.instance)

        if form.is_valid() and formset.is_valid():
            return self._save_all(form, formset)

        return self.render_to_response(self.get_context_data(form=form, imagenes_formset=formset))

    def _save_all(self, form, formset):
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
        messages.success(self.request, "Producto guardado correctamente.")
        return redirect(self.get_success_url())

class ProductoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "inventario/producto_form.html"
    permission_required = "inventario.change_producto"

    def get_success_url(self):
        return reverse("inventario:producto_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = "productos"
        if "imagenes_formset" not in ctx:
            ctx["imagenes_formset"] = ProductoImagenInlineFormSet(instance=self.object)
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = ProductoImagenInlineFormSet(self.request.POST, self.request.FILES, instance=self.object)

        if form.is_valid() and formset.is_valid():
            return self._save_all(form, formset)

        return self.render_to_response(self.get_context_data(form=form, imagenes_formset=formset))

    def _save_all(self, form, formset):
        with transaction.atomic():
            self.object = form.save()
            formset.save()

        messages.success(self.request, "Producto actualizado correctamente.")
        return redirect(self.get_success_url())



class ProductoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Producto
    template_name = "inventario/producto_confirm_delete.html"
    permission_required = "inventario.delete_producto"

    def get_success_url(self):
        return reverse("inventario:producto_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = "productos"
        return ctx


class ProductoHistorialView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Producto
    template_name = "inventario/producto_historial.html"
    permission_required = "inventario.view_producto"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        movimientos = (
            MovimientoStock.objects.filter(producto=self.object)
            .select_related("ubicacion", "proveedor", "usuario")
            .order_by("-fecha", "-id")[:200]
        )
        stocks = StockActual.objects.filter(producto=self.object).select_related("ubicacion").order_by("ubicacion__codigo")
        ctx["movimientos"] = movimientos
        ctx["stocks"] = stocks
        ctx["active_tab"] = "productos"
        ctx["imagenes"] = self.object.imagenes.all()
        return ctx


@login_required
@permission_required("inventario.can_export_productos", raise_exception=True)
def productos_export_csv(request):
    resource = ProductoResource()
    dataset = resource.export(Producto.objects.all().order_by("codigo"))
    csv_bytes = dataset.csv.encode("utf-8")

    resp = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="productos_export.csv"'
    return resp


@login_required
@permission_required("inventario.can_import_productos", raise_exception=True)
def productos_import_csv(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "No se seleccionó ningón archivo.")
            return redirect("inventario:producto_import")

        raw = file.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "El archivo no estó en UTF-8. Guardalo como UTF-8 y reintentó.")
            return redirect("inventario:producto_import")

        dataset = Dataset().load(text, format="csv")
        resource = ProductoResource()

        result = resource.import_data(dataset, dry_run=True, raise_errors=False)
        if result.has_errors():
            messages.error(request, "El archivo tiene errores. Revisó columnas/formatos.")
            pretty = []
            for row_idx, row_errs in result.row_errors():
                pretty.append({"row": row_idx, "errors": [str(e.error) for e in row_errs]})
            return render(request, "inventario/producto_import.html", {"preview_errors": pretty, "active_tab": "productos"})

        resource.import_data(dataset, dry_run=False, raise_errors=False)
        messages.success(request, "Importación realizada correctamente.")
        return redirect("inventario:producto_list")

    return render(request, "inventario/producto_import.html", {"active_tab": "productos"})


# -----------------------------
# Stock actual
# -----------------------------
class StockActualListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StockActual
    template_name = "inventario/stock_list.html"
    paginate_by = 30
    permission_required = "inventario.view_stockactual"

    def get_queryset(self):
        qs = super().get_queryset().select_related("producto", "ubicacion", "producto__unidad_medida")
        self.filterset = StockActualFilter(self.request.GET, queryset=qs)
        qs = self.filterset.qs

        # Low stock toggle: ólow=1
        if self.request.GET.get("low") in ("1", "true", "True", "on"):
            qs = qs.filter(cantidad__lt=F("producto__stock_minimo"))

        return qs.order_by("producto__codigo", "ubicacion__codigo")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filterset"] = self.filterset
        ctx["active_tab"] = "stock"
        ctx["low"] = self.request.GET.get("low") in ("1", "true", "True", "on")
        return ctx


# -----------------------------
# Movimientos
# -----------------------------
class MovimientoStockListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "inventario.view_movimientostock"
    model = MovimientoStock
    template_name = "inventario/movimiento_list.html"
    context_object_name = "movimientos"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related("producto", "ubicacion", "ubicacion_destino", "proveedor", "colectivo", "usuario").order_by("-fecha")
        self.filterset = MovimientoStockFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filterset"] = getattr(self, "filterset", None)
        ctx["active_tab"] = "movimientos"
        return ctx

class MovimientoStockCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = MovimientoStock
    form_class = MovimientoStockForm
    template_name = "inventario/movimiento_form.html"
    permission_required = "inventario.can_manage_stock"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request_user"] = self.request.user
        return kw

    def get_initial(self):
        initial = super().get_initial()

        tipo = (self.request.GET.get("tipo") or "").strip().upper()
        valid_tipos = {k for k, _ in MovimientoStock.Tipo.choices}
        if tipo in valid_tipos:
            initial["tipo"] = tipo

        col_raw = self.request.GET.get("colectivo") or self.request.GET.get("colectivo_id")
        col_id = None
        try:
            if col_raw:
                col_id = int(col_raw)
        except Exception:
            col_id = None

        if col_id:
            initial["colectivo"] = col_id

            ref = (self.request.GET.get("ref") or self.request.GET.get("referencia") or "").strip()
            if not ref:
                try:
                    c = Colectivo.objects.only("interno").get(pk=col_id)
                    initial["referencia"] = f"INT-{c.interno}"
                except Colectivo.DoesNotExist:
                    pass
            else:
                initial["referencia"] = ref

        return initial

    def get_success_url(self):
        next_url = (self.request.POST.get("next") or self.request.GET.get("next") or "").strip()
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse("inventario:movimiento_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = "movimientos"
        ctx["next"] = (self.request.POST.get("next") or self.request.GET.get("next") or "").strip()
        return ctx

    def form_invalid(self, form):
        # Cartel general (además de los errores de campo)
        messages.error(self.request, "No se pudo guardar el movimiento. Revisá los campos marcados.")
        return super().form_invalid(form)

    def form_valid(self, form):
        """
        Crea movimiento + aplica stock.

        Importante: si venís del informe de una unidad con force=1, forzamos colectivo_id aunque el usuario no lo toque.
        """
        try:
            with transaction.atomic():
                # Forzar unidad cuando viene del informe (evita que quede NULL por error humano)
                force = (self.request.GET.get("force") or "").strip() in ("1", "true", "True", "on")
                col_raw = self.request.GET.get("colectivo") or self.request.GET.get("colectivo_id")
                col_id = None
                try:
                    if col_raw:
                        col_id = int(col_raw)
                except Exception:
                    col_id = None

                if force and col_id and not getattr(form.instance, "colectivo_id", None):
                    form.instance.colectivo_id = col_id

                response = super().form_valid(form)

                # Aplica stock
                stock_service.aplicar_movimiento_creado(self.object)

                messages.success(self.request, "Movimiento registrado correctamente.")
                return response

        except ValueError as e:
            # Error típico: stock insuficiente / transferencia sin destino / etc.
            messages.error(self.request, str(e))
            form.add_error(None, str(e))
            return self.form_invalid(form)

class MovimientoStockUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "inventario.change_movimientostock"
    model = MovimientoStock
    form_class = MovimientoStockForm
    template_name = "inventario/movimiento_form.html"
    success_url = reverse_lazy("inventario:movimiento_list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request_user"] = self.request.user
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = "movimientos"
        return ctx

    def form_valid(self, form):
        """
        Editar movimiento: recalcula stock correctamente.

        Proceso:
        1) Bloquea el movimiento viejo (select_for_update)
        2) Guarda snapshot del movimiento viejo
        3) Guarda el movimiento nuevo (super().form_valid)
        4) Aplica delta de stock en base al snapshot vs nuevo

        Nota: el vínculo a unidad (colectivo) NO afecta stock, solo trazabilidad.
        """
        try:
            with transaction.atomic():
                old_obj = MovimientoStock.objects.select_for_update().get(pk=self.object.pk)

                old = stock_service.MovimientoSnapshot(
                    producto_id=old_obj.producto_id,
                    ubicacion_id=old_obj.ubicacion_id,
                    tipo=old_obj.tipo,
                    cantidad=old_obj.cantidad,
                    # Si tu snapshot soporta destino (transferencias), lo pasamos.
                    # Si no existe ese parámetro en tu clase, borrá estas 2 líneas.
                    ubicacion_destino_id=getattr(old_obj, "ubicacion_destino_id", None),
                )

                response = super().form_valid(form)

                # Aplica el ajuste (delta) al stock
                stock_service.aplicar_movimiento_actualizado(old, self.object)

                return response
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)


class MovimientoStockDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "inventario.delete_movimientostock"
    model = MovimientoStock
    template_name = "inventario/movimiento_confirm_delete.html"
    success_url = reverse_lazy("inventario:movimiento_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = "movimientos"
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                obj = MovimientoStock.objects.select_for_update().get(pk=self.object.pk)
                stock_service.aplicar_movimiento_eliminado(obj)
                obj.delete()
            return redirect(self.success_url)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect(self.success_url)


#-------------------------------
# INVIENTARIO PDF
#-----------------------------
@login_required
@permission_required("inventario.view_producto", raise_exception=True)
def productos_etiquetas_pdf(request):
    if not REPORTLAB_OK:
        messages.error(request, "No está instalado el módulo 'reportlab'. Instalalo para imprimir etiquetas.")
        return redirect("inventario:producto_list")

    """
    Genera PDF A4 con etiquetas Code128 del código interno.
    Respeta filtros por querystring (mismos que la lista de productos).
    """
    

    qs = Producto.objects.filter(is_active=True).order_by("codigo")
    filterset = ProductoFilter(request.GET, queryset=qs)
    qs = filterset.qs.order_by("codigo")

    buff = BytesIO()
    c = canvas.Canvas(buff, pagesize=A4)
    pw, ph = A4

    # Grid de etiquetas (A4): 3 columnas x 8 filas
    cols = 3
    rows = 8

    margin_x = 8 * mm
    margin_y = 10 * mm
    gap_x = 4 * mm
    gap_y = 4 * mm

    label_w = (pw - 2 * margin_x - (cols - 1) * gap_x) / cols
    label_h = (ph - 2 * margin_y - (rows - 1) * gap_y) / rows

    def draw_label(x, y, codigo, nombre):
        # marco suave (opcional)
        # c.rect(x, y, label_w, label_h, stroke=1, fill=0)

        # texto
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 4, y + label_h - 12, codigo[:32])

        c.setFont("Helvetica", 7)
        nombre_txt = (nombre or "").strip()
        if len(nombre_txt) > 40:
            nombre_txt = nombre_txt[:37] + "..."
        c.drawString(x + 4, y + label_h - 22, nombre_txt)

        # barcode
        barcode = code128.Code128(codigo, barHeight=10 * mm, humanReadable=False)
        bx = x + 4
        by = y + 4
        barcode.drawOn(c, bx, by)

    i = 0
    for p in qs.iterator():
        col = i % cols
        row = (i // cols) % rows
        page = i // (cols * rows)

        if i > 0 and (i % (cols * rows) == 0):
            c.showPage()

        x = margin_x + col * (label_w + gap_x)
        y = ph - margin_y - (row + 1) * label_h - row * gap_y
        draw_label(x, y, p.codigo, p.nombre)

        i += 1

    if i == 0:
        c.setFont("Helvetica", 10)
        c.drawString(40, ph - 40, "No hay productos para imprimir con los filtros aplicados.")

    c.save()
    pdf = buff.getvalue()
    buff.close()

    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'inline; filename="etiquetas_productos.pdf"'
    return resp