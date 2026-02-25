from __future__ import annotations

import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from adjuntos.models import ProductoImagen
from inventario.models import Producto


class ProductoImagenTests(TestCase):
    def test_crear_imagen_y_asociar_a_producto(self):
        tmpdir = tempfile.mkdtemp(prefix="panol_media_")
        try:
            with override_settings(MEDIA_ROOT=tmpdir):
                p = Producto.objects.create(codigo="P-IMG", nombre="Producto con imagen")

                uploaded = SimpleUploadedFile(
                    "foto.jpg",
                    b"fake-image-bytes",
                    content_type="image/jpeg",
                )

                img = ProductoImagen.objects.create(producto=p, imagen=uploaded, titulo="Frente", orden=1)

                self.assertEqual(img.producto_id, p.id)
                self.assertTrue(p.imagenes.exists())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
