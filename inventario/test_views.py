from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from adjuntos.forms import ProductoImagenInlineFormSet
from adjuntos.models import ProductoImagen
from inventario.models import (
    Categoria,
    Subcategoria,
    UnidadMedida,
    Proveedor,
    Ubicacion,
    Producto,
)


class InventarioViewsSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_superuser(username="admin", password="pass1234", email="admin@example.com")

        cls.cat = Categoria.objects.create(nombre="Cat A")
        cls.sub = Subcategoria.objects.create(nombre="Sub A", categoria=cls.cat)
        cls.um = UnidadMedida.objects.create(nombre="Unidad", abreviatura="u")
        cls.prov = Proveedor.objects.create(nombre="Prov A")
        cls.ubi = Ubicacion.objects.create(codigo="DP-A01", nombre="Depósito A")

        cls.prod = Producto.objects.create(
            codigo="P-001",
            nombre="Producto A",
            descripcion="",
            categoria=cls.cat,
            subcategoria=cls.sub,
            unidad_medida=cls.um,
            proveedor=cls.prov,
            stock_minimo=Decimal("0.000"),
            maneja_vencimiento=False,
            is_active=True,
        )

    def setUp(self):
        self.client.login(username="admin", password="pass1234")

    def test_movimiento_list_loads(self):
        resp = self.client.get(reverse("inventario:movimiento_list"))
        self.assertEqual(resp.status_code, 200)

    def test_movimiento_create_loads(self):
        resp = self.client.get(reverse("inventario:movimiento_create"))
        self.assertEqual(resp.status_code, 200)

    def test_product_update_loads(self):
        resp = self.client.get(reverse("inventario:producto_update", args=[self.prod.id]))
        self.assertEqual(resp.status_code, 200)

    def test_product_historial_loads(self):
        resp = self.client.get(reverse("inventario:producto_historial", args=[self.prod.id]))
        self.assertEqual(resp.status_code, 200)

    def test_product_update_can_add_image_and_historial_lists_it(self):
        url_update = reverse("inventario:producto_update", args=[self.prod.id])

        # Prefix real del inline formset (clave para armar el POST)
        fs0 = ProductoImagenInlineFormSet(instance=self.prod)
        prefix = fs0.prefix

        img = SimpleUploadedFile(
            "test.png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 32,
            content_type="image/png",
        )

        data = {
            # Form de ProductoForm
            "codigo": self.prod.codigo,
            "nombre": self.prod.nombre,
            "descripcion": self.prod.descripcion,
            "categoria": str(self.cat.id),
            "subcategoria": str(self.sub.id),
            "unidad_medida": str(self.um.id),
            "proveedor": str(self.prov.id),
            "stock_minimo": "0.000",
            "maneja_vencimiento": "",
            "is_active": "on",

            # Management form del formset
            f"{prefix}-TOTAL_FORMS": "2",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",

            # Form 0 (con imagen)
            f"{prefix}-0-imagen": img,
            f"{prefix}-0-titulo": "Foto 1",
            f"{prefix}-0-orden": "1",

            # Form 1 (vacío)
            f"{prefix}-1-imagen": "",
            f"{prefix}-1-titulo": "",
            f"{prefix}-1-orden": "",
        }

        resp = self.client.post(url_update, data=data, follow=True)
        self.assertEqual(resp.status_code, 200)

        self.assertGreaterEqual(ProductoImagen.objects.filter(producto=self.prod).count(), 1)

        url_hist = reverse("inventario:producto_historial", args=[self.prod.id])
        resp2 = self.client.get(url_hist)
        self.assertEqual(resp2.status_code, 200)


    def test_product_update_can_add_image_without_orden(self):
        url_update = reverse("inventario:producto_update", args=[self.prod.id])

        fs0 = ProductoImagenInlineFormSet(instance=self.prod)
        prefix = fs0.prefix

        img = SimpleUploadedFile(
            "test2.png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 32,
            content_type="image/png",
        )

        data = {
            "codigo": self.prod.codigo,
            "nombre": self.prod.nombre,
            "descripcion": self.prod.descripcion,
            "categoria": str(self.cat.id),
            "subcategoria": str(self.sub.id),
            "unidad_medida": str(self.um.id),
            "proveedor": str(self.prov.id),
            "stock_minimo": "0.000",
            "maneja_vencimiento": "",
            "is_active": "on",

            f"{prefix}-TOTAL_FORMS": "2",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",

            f"{prefix}-0-imagen": img,
            f"{prefix}-0-titulo": "Foto sin orden",
            f"{prefix}-0-orden": "",

            f"{prefix}-1-imagen": "",
            f"{prefix}-1-titulo": "",
            f"{prefix}-1-orden": "",
        }

        resp = self.client.post(url_update, data=data, follow=True)
        self.assertEqual(resp.status_code, 200)

        obj = ProductoImagen.objects.filter(producto=self.prod).order_by("id").last()
        self.assertIsNotNone(obj)
        self.assertIsNotNone(obj.orden)
        self.assertGreaterEqual(int(obj.orden), 1)
