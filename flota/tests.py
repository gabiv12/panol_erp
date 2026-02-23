from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from flota.models import Colectivo


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
