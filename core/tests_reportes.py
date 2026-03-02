from __future__ import annotations

import os
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from auditoria.models import AuditEvent


class ReporteGerenciaCommandTests(TestCase):
    def test_send_report_gerencia_generates_files(self):
        # Crear algunos eventos mínimos
        AuditEvent.objects.create(method="GET", path="/dashboard/", username="user_a", app_area="core", action="view", status_code=200, duration_ms=120)
        AuditEvent.objects.create(method="GET", path="/flota/colectivos/", username="user_a", app_area="flota", action="view", status_code=200, duration_ms=250)

        with tempfile.TemporaryDirectory() as td:
            outdir = Path(td)
            call_command("send_report_gerencia", period="daily", outdir=str(outdir))

            # Debe haber al menos 4 archivos (txt + 3 csv)
            files = list(outdir.glob("informe_daily_*.txt"))
            self.assertTrue(files, "No se generó el TXT de informe")

            empleados = list(outdir.glob("informe_daily_*_empleados.csv"))
            dispositivos = list(outdir.glob("informe_daily_*_dispositivos.csv"))
            areas = list(outdir.glob("informe_daily_*_areas.csv"))

            self.assertTrue(empleados, "No se generó empleados.csv")
            self.assertTrue(dispositivos, "No se generó dispositivos.csv")
            self.assertTrue(areas, "No se generó areas.csv")
