from __future__ import annotations

from datetime import timedelta

import shutil
import tempfile

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from flota.models import Colectivo
from flota.partes_models import ParteDiario, ParteDiarioAdjunto


class FlotaPermissionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user_a", password="pass12345")

    def test_list_requires_login(self):
        resp = self.client.get(reverse("flota:colectivo_list"))
        self.assertEqual(resp.status_code, 302)

    def test_list_requires_permission(self):
        self.client.login(username="user_a", password="pass12345")
        resp = self.client.get(reverse("flota:colectivo_list"))
        self.assertEqual(resp.status_code, 403)

    def test_list_ok_with_view_permission(self):
        ct = ContentType.objects.get_for_model(Colectivo)
        perm = Permission.objects.get(content_type=ct, codename="view_colectivo")
        self.user.user_permissions.add(perm)

        self.client.login(username="user_a", password="pass12345")
        resp = self.client.get(reverse("flota:colectivo_list"))
        self.assertEqual(resp.status_code, 200)


class PartesDiariosTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="admin12345", email="admin@example.com")
        self.client.login(username="admin", password="admin12345")

        self.c = Colectivo.objects.create(
            interno=10,
            dominio="AAA111",
            anio_modelo=2015,
            marca="Marca",
            modelo="Modelo",
            numero_chasis="CHASIS10",
            is_active=True,
        )

    def test_parte_create_list_detail(self):
        # Crear parte por POST
        dt_local = timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M")
        resp = self.client.post(
            reverse("flota:parte_create"),
            data={
                "colectivo": self.c.id,
                "fecha_evento": dt_local,
                "tipo": ParteDiario.Tipo.INCIDENCIA,
                "severidad": ParteDiario.Severidad.MEDIA,
                "estado": ParteDiario.Estado.ABIERTO,
                "descripcion": "Incidencia de prueba",
                "observaciones": "",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        parte = ParteDiario.objects.latest("id")

        # Lista general
        resp_list = self.client.get(reverse("flota:parte_list"))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, "Incidencia de prueba")

        # Detalle
        resp_det = self.client.get(reverse("flota:parte_detail", args=[parte.id]))
        self.assertEqual(resp_det.status_code, 200)
        self.assertContains(resp_det, f"Parte diario #{parte.id}")

    def test_duracion_auxilio_min(self):
        ini = timezone.now()
        fin = ini + timedelta(minutes=37)

        parte = ParteDiario.objects.create(
            colectivo=self.c,
            tipo=ParteDiario.Tipo.AUXILIO,
            severidad=ParteDiario.Severidad.ALTA,
            estado=ParteDiario.Estado.EN_PROCESO,
            fecha_evento=ini,
            auxilio_inicio=ini,
            auxilio_fin=fin,
            descripcion="Auxilio de prueba",
        )
        self.assertEqual(parte.duracion_auxilio_min, 37)

    def test_adjunto_add(self):
        tmpdir = tempfile.mkdtemp(prefix="panol_media_")
        try:
            with override_settings(MEDIA_ROOT=tmpdir):
                parte = ParteDiario.objects.create(
                    colectivo=self.c,
                    tipo=ParteDiario.Tipo.CHECKLIST,
                    severidad=ParteDiario.Severidad.BAJA,
                    estado=ParteDiario.Estado.ABIERTO,
                    descripcion="Checklist",
                )

                uploaded = SimpleUploadedFile(
                    "evidencia.jpg",
                    b"fake-image-bytes",
                    content_type="image/jpeg",
                )

                resp = self.client.post(
                    reverse("flota:parte_adjunto_add", args=[parte.id]),
                    data={"archivo": uploaded, "descripcion": "Foto"},
                    follow=True,
                )
                self.assertEqual(resp.status_code, 200)

                self.assertTrue(ParteDiarioAdjunto.objects.filter(parte=parte).exists())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class FlotaPlan15SmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.user.is_staff = True
        self.user.save()
        self.client.login(username="u", password="p")

    def test_plan_15_get(self):
        url = reverse("flota:plan_15")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_informe_get(self):
        url = reverse("flota:informe_flota")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
