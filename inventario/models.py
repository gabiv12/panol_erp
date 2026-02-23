from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        abstract = True


class Categoria(TimeStampedModel):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre

    def clean(self):
        super().clean()
        if self.nombre:
            self.nombre = self.nombre.strip()


class Subcategoria(TimeStampedModel):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="subcategorias")
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "subcategoría"
        verbose_name_plural = "subcategorías"
        ordering = ["categoria__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["categoria", "nombre"], name="uq_subcategoria_categoria_nombre"),
        ]

    def __str__(self) -> str:
        return f"{self.categoria.nombre} · {self.nombre}"

    def clean(self):
        super().clean()
        if self.nombre:
            self.nombre = self.nombre.strip()


class UnidadMedida(TimeStampedModel):
    nombre = models.CharField(max_length=80, unique=True)
    abreviatura = models.CharField(max_length=12, unique=True)
    permite_decimales = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "unidad de medida"
        verbose_name_plural = "unidades de medida"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.abreviatura})"

    def clean(self):
        super().clean()
        if self.nombre:
            self.nombre = self.nombre.strip()
        if self.abreviatura:
            self.abreviatura = self.abreviatura.strip()


class Proveedor(TimeStampedModel):
    nombre = models.CharField(max_length=180)
    cuit = models.CharField(max_length=20, blank=True, null=True, unique=True)
    telefono = models.CharField(max_length=60, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"], name="idx_proveedor_nombre"),
        ]

    def __str__(self) -> str:
        return self.nombre

    def clean(self):
        super().clean()
        if self.nombre:
            self.nombre = self.nombre.strip()
        if self.cuit is not None:
            v = str(self.cuit).strip()
            self.cuit = v if v else None


class Ubicacion(TimeStampedModel):
    """Ubicación física.

    Mantiene el campo `codigo` (único) para que el usuario pueda buscar/etiquetar.

    Se agregan campos opcionales para representar el layout del depósito:
    pasillo / módulo / nivel / posición y una jerarquía simple por `padre`.

    Importante: Estos campos son opcionales y no rompen el flujo actual.
    """

    class Tipo(models.TextChoices):
        DEPOSITO = "DEPOSITO", "Depósito"
        UBICACION = "UBICACION", "Ubicación"
        ZONA = "ZONA", "Zona"
        OTRO = "OTRO", "Otro"

    codigo = models.CharField(max_length=60, unique=True, help_text="Código único. Ej: DP-A01-M01-N01-P01")
    nombre = models.CharField(max_length=160, blank=True, default="")
    tipo = models.CharField(max_length=14, choices=Tipo.choices, default=Tipo.UBICACION)

    padre = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="hijos",
    )

    pasillo = models.CharField(max_length=20, blank=True, default="")
    modulo = models.SmallIntegerField(blank=True, null=True)
    nivel = models.SmallIntegerField(blank=True, null=True)
    posicion = models.SmallIntegerField(blank=True, null=True)

    permite_transferencias = models.BooleanField(default=True)
    referencia = models.CharField(max_length=120, blank=True)
    descripcion = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"
        ordering = ["codigo"]
        indexes = [
            models.Index(fields=["codigo"], name="idx_ubicacion_codigo"),
            models.Index(fields=["tipo"], name="idx_ubicacion_tipo"),
        ]

    def __str__(self) -> str:
        return self.codigo

    def clean(self):
        super().clean()
        if self.codigo:
            self.codigo = self.codigo.strip().upper()
        if self.pasillo:
            self.pasillo = self.pasillo.strip().upper()
        if self.referencia:
            self.referencia = self.referencia.strip()


class Producto(TimeStampedModel):
    codigo = models.CharField(max_length=60, unique=True)
    nombre = models.CharField(max_length=220)
    descripcion = models.TextField(blank=True)

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos", blank=True, null=True)
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.PROTECT, related_name="productos", blank=True, null=True)
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.PROTECT, related_name="productos", blank=True, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="productos", blank=True, null=True)

    stock_minimo = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    maneja_vencimiento = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["codigo"]
        indexes = [
            models.Index(fields=["codigo"], name="idx_producto_codigo"),
            models.Index(fields=["nombre"], name="idx_producto_nombre"),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"

    def clean(self):
        super().clean()
        if self.codigo:
            self.codigo = self.codigo.strip().upper()
        if self.nombre:
            self.nombre = self.nombre.strip()


class StockActual(TimeStampedModel):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="stocks")
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, related_name="stocks")
    cantidad = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    last_movement_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "stock actual"
        verbose_name_plural = "stock actual"
        constraints = [
            models.UniqueConstraint(fields=["producto", "ubicacion"], name="uq_stock_producto_ubicacion"),
        ]
        indexes = [
            models.Index(fields=["producto"], name="idx_stock_producto"),
            models.Index(fields=["ubicacion"], name="idx_stock_ubicacion"),
        ]

    def __str__(self) -> str:
        return f"{self.producto.codigo} @ {self.ubicacion.codigo}: {self.cantidad}"


class MovimientoStock(TimeStampedModel):
    class Tipo(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        EGRESO = "EGRESO", "Egreso"
        AJUSTE = "AJUSTE", "Ajuste"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="movimientos")
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, related_name="movimientos")

    colectivo = models.ForeignKey(
    "flota.Colectivo",
    on_delete=models.SET_NULL,
    blank=True,
    null=True,
    related_name="movimientos_stock",
)

    # NUEVO: vínculo a unidad (opcional) para informes y trazabilidad real
    colectivo = models.ForeignKey(
        "flota.Colectivo",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="movimientos_stock",
    )

    tipo = models.CharField(max_length=14, choices=Tipo.choices)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    fecha = models.DateTimeField("fecha", auto_now_add=True)

    ubicacion_destino = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name="movimientos_destino",
        blank=True,
        null=True,
    )

    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="movimientos", blank=True, null=True)
    referencia = models.CharField(max_length=120, blank=True)
    observaciones = models.TextField(blank=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="movimientos_stock",
    )

    lote = models.CharField(max_length=80, blank=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = "movimiento de stock"
        verbose_name_plural = "movimientos de stock"
        ordering = ["-fecha", "-id"]
        indexes = [
            models.Index(fields=["producto", "fecha"], name="idx_mov_producto_fecha"),
            models.Index(fields=["ubicacion", "fecha"], name="idx_mov_ubicacion_fecha"),
            models.Index(fields=["tipo", "fecha"], name="idx_mov_tipo_fecha"),
        ]

    def __str__(self) -> str:
        if self.tipo == self.Tipo.TRANSFERENCIA and self.ubicacion_destino_id:
            return f"{self.tipo} {self.producto.codigo} {self.cantidad} ({self.ubicacion.codigo} -> {self.ubicacion_destino.codigo})"
        return f"{self.tipo} {self.producto.codigo} {self.cantidad} ({self.ubicacion.codigo})"

    def clean(self):
        super().clean()
        if self.referencia:
            self.referencia = self.referencia.strip()
        if self.lote:
            self.lote = self.lote.strip()

        try:
            qty = Decimal(self.cantidad)
        except Exception:
            return

        if self.tipo in (self.Tipo.INGRESO, self.Tipo.EGRESO, self.Tipo.TRANSFERENCIA):
            if qty <= 0:
                raise ValidationError({"cantidad": "La cantidad debe ser mayor a 0."})
        elif self.tipo == self.Tipo.AJUSTE:
            if qty == 0:
                raise ValidationError({"cantidad": "El ajuste no puede ser 0."})

        if self.tipo == self.Tipo.TRANSFERENCIA:
            if not self.ubicacion_destino_id:
                raise ValidationError({"ubicacion_destino": "La transferencia requiere una ubicación destino."})
            if self.ubicacion_destino_id == self.ubicacion_id:
                raise ValidationError({"ubicacion_destino": "La ubicación destino debe ser distinta a la de origen."})
            if getattr(self.ubicacion, "permite_transferencias", True) is False:
                raise ValidationError({"ubicacion": "La ubicación origen no permite transferencias."})
            if getattr(self.ubicacion_destino, "permite_transferencias", True) is False:
                raise ValidationError({"ubicacion_destino": "La ubicación destino no permite transferencias."})
        else:
            self.ubicacion_destino = None