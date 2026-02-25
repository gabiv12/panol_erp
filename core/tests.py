from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from flota.models import Colectivo


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user_a", password="pass12345")

    def test_dashboard_redirects_when_not_logged(self):
        url = reverse("core:dashboard")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_ok_logged(self):
        self.client.login(username="user_a", password="pass12345")
        url = reverse("core:dashboard")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_counts(self):
        today = timezone.localdate()

        # Sin fecha
        Colectivo.objects.create(
            interno=100,
            dominio="AAA111",
            anio_modelo=2010,
            marca="X",
            modelo="Y",
            numero_chasis="CHASIS100",
            revision_tecnica_vto=None,
            is_active=True,
        )

        # Vencido
        Colectivo.objects.create(
            interno=101,
            dominio="BBB222",
            anio_modelo=2010,
            marca="X",
            modelo="Y",
            numero_chasis="CHASIS101",
            revision_tecnica_vto=today - timedelta(days=1),
            is_active=True,
        )

        # Por vencer (<= 7 días)
        Colectivo.objects.create(
            interno=102,
            dominio="CCC333",
            anio_modelo=2010,
            marca="X",
            modelo="Y",
            numero_chasis="CHASIS102",
            revision_tecnica_vto=today + timedelta(days=3),
            is_active=True,
        )

        self.client.login(username="user_a", password="pass12345")
        resp = self.client.get(reverse("core:dashboard"))

        # Título del bloque
        self.assertContains(resp, "Vencimientos VTV")

        # Estados esperados en la tabla
        self.assertContains(resp, "Vencido")
        self.assertContains(resp, "Por vencer")
        self.assertContains(resp, "Pendiente")

        # Internos presentes
        self.assertContains(resp, "100")
        self.assertContains(resp, "101")
        self.assertContains(resp, "102")
