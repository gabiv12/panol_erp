from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class PreflightConfigTests(TestCase):
    """Checks rápidos para evitar "sorpresas" antes de producción local-first.

    No reemplaza check --deploy, pero asegura:
    - TZ / idioma consistentes
    - CSS offline existe
    - Login renderiza
    """

    def test_settings_basics(self):
        self.assertEqual(settings.LANGUAGE_CODE, "es-ar")
        self.assertEqual(settings.TIME_ZONE, "America/Argentina/Cordoba")
        self.assertTrue(getattr(settings, "USE_TZ", False))

    def test_offline_css_exists(self):
        base_dir = Path(getattr(settings, "BASE_DIR"))
        css = base_dir / "static" / "css" / "dist" / "styles.css"
        self.assertTrue(
            css.exists(),
            f"No existe {css}. Corré: npm install ; npm run tw:build",
        )

    def test_login_page_renders(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Iniciar sesión")
