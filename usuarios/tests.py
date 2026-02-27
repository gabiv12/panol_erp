from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.permissions import ROLE_ADMIN, ROLE_CHOFER


class UsuariosAdminViewsTests(TestCase):
    """Tests mínimos para el módulo Administración > Usuarios.

    Alcance:
    - Login requerido
    - Superusuario requerido
    - Formularios (alta/edición/eliminación) con rol + módulos
    """

    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="admin12345", email="admin@example.com")

    def test_list_requires_login(self):
        resp = self.client.get(reverse("usuarios:usuario_list"))
        self.assertEqual(resp.status_code, 302)

    def test_list_requires_superuser(self):
        User.objects.create_user(username="staff", password="x12345", is_staff=True)
        self.client.login(username="staff", password="x12345")
        resp = self.client.get(reverse("usuarios:usuario_list"))
        self.assertEqual(resp.status_code, 302)

    def test_list_ok_when_superuser(self):
        self.client.login(username="admin", password="admin12345")
        resp = self.client.get(reverse("usuarios:usuario_list"))
        self.assertEqual(resp.status_code, 200)

    def test_create_user_sets_password_and_can_login(self):
        self.client.login(username="admin", password="admin12345")

        resp = self.client.post(
            reverse("usuarios:usuario_create"),
            data={
                "role": ROLE_CHOFER,
                "modules": [],
                "username": "user_b",
                "first_name": "Usuario",
                "last_name": "B",
                "email": "user_b@example.com",
                "is_active": "on",
                "is_staff": "",
                "password1": "pass12345!",
                "password2": "pass12345!",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.filter(username="user_b").exists())

        self.client.logout()
        ok = self.client.login(username="user_b", password="pass12345!")
        self.assertTrue(ok)

    def test_update_user_password_optional(self):
        u = User.objects.create_user(username="user_c", password="oldpass123")

        self.client.login(username="admin", password="admin12345")

        resp = self.client.post(
            reverse("usuarios:usuario_update", args=[u.id]),
            data={
                "role": ROLE_CHOFER,
                "modules": [],
                "username": "user_c",
                "first_name": "",
                "last_name": "",
                "email": "",
                "is_active": "on",
                "is_staff": "",
                "password1": "",
                "password2": "",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)

        self.client.logout()
        self.assertTrue(self.client.login(username="user_c", password="oldpass123"))

        self.client.logout()
        self.client.login(username="admin", password="admin12345")
        resp = self.client.post(
            reverse("usuarios:usuario_update", args=[u.id]),
            data={
                "role": ROLE_CHOFER,
                "modules": [],
                "username": "user_c",
                "first_name": "",
                "last_name": "",
                "email": "",
                "is_active": "on",
                "is_staff": "",
                "password1": "newpass123",
                "password2": "newpass123",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)

        self.client.logout()
        self.assertTrue(self.client.login(username="user_c", password="newpass123"))

    def test_delete_user(self):
        u = User.objects.create_user(username="user_del", password="pass123")
        self.client.login(username="admin", password="admin12345")

        resp = self.client.get(reverse("usuarios:usuario_delete", args=[u.id]))
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(reverse("usuarios:usuario_delete", args=[u.id]), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="user_del").exists())

    def test_search_filter(self):
        User.objects.create_user(username="alpha")
        User.objects.create_user(username="beta")

        self.client.login(username="admin", password="admin12345")
        resp = self.client.get(reverse("usuarios:usuario_list") + "?q=bet")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "beta")
        self.assertNotContains(resp, "alpha")
