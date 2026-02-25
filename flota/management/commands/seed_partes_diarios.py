from __future__ import annotations

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from flota.models import Colectivo
from flota.partes_models import ParteDiario


class Command(BaseCommand):
    help = "Crea datos de ejemplo para Partes diarios (realistas) para pruebas/demo."

    def add_arguments(self, parser):
        parser.add_argument("--colectivos", type=int, default=10)
        parser.add_argument("--partes", type=int, default=50)
        parser.add_argument("--dias", type=int, default=30)

    def handle(self, *args, **opts):
        n_colectivos = int(opts["colectivos"])
        n_partes = int(opts["partes"])
        dias = int(opts["dias"])

        # 1) Colectivos: crear si faltan
        actuales = Colectivo.objects.count()
        if actuales < n_colectivos:
            faltan = n_colectivos - actuales
            self.stdout.write(self.style.WARNING(f"Creando {faltan} colectivos de ejemplo..."))
            base_interno = (Colectivo.objects.order_by("-interno").first().interno if Colectivo.objects.exists() else 100)

            for i in range(faltan):
                interno = base_interno + i + 1
                Colectivo.objects.create(
                    interno=interno,
                    dominio=f"TEST{interno}",
                    anio_modelo=2015 + (i % 8),
                    marca="Marca",
                    modelo="Modelo",
                    numero_chasis=f"CH{interno}{i}",
                    is_active=True,
                )

        colectivos = list(Colectivo.objects.filter(is_active=True))
        if not colectivos:
            raise Exception("No hay colectivos activos para asignar partes.")

        # Campos opcionales según tu modelo real
        parte_fields = {f.name for f in ParteDiario._meta.fields}

        tipos = [c[0] for c in ParteDiario.Tipo.choices]
        estados = [c[0] for c in ParteDiario.Estado.choices]
        severidades = [c[0] for c in ParteDiario.Severidad.choices]

        now = timezone.now()
        creados = 0

        for _ in range(n_partes):
            c = random.choice(colectivos)

            # fecha en los últimos N días, con hora razonable
            d = random.randint(0, max(dias - 1, 0))
            hora = random.randint(6, 20)
            minuto = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
            fecha_evento = (now - timedelta(days=d)).replace(hour=hora, minute=minuto, second=0, microsecond=0)

            tipo = random.choice(tipos)
            estado = random.choice(estados)
            sev = random.choice(severidades)

            data = dict(
                colectivo=c,
                fecha_evento=fecha_evento,
                tipo=tipo,
                estado=estado,
                severidad=sev,
                descripcion=f"{tipo}: Parte generado para pruebas",
                observaciones="Generado automáticamente para demo/pruebas.",
            )

            # Odómetro si existe
            if "odometro" in parte_fields:
                data["odometro"] = random.randint(50000, 250000)

            # Auxilio: setear inicio/fin si existen
            if tipo == getattr(ParteDiario.Tipo, "AUXILIO", "AUXILIO"):
                if "auxilio_inicio" in parte_fields:
                    data["auxilio_inicio"] = fecha_evento
                if "auxilio_fin" in parte_fields:
                    data["auxilio_fin"] = fecha_evento + timedelta(minutes=random.randint(15, 120))

            ParteDiario.objects.create(**data)
            creados += 1

        self.stdout.write(self.style.SUCCESS(f"OK: {creados} partes creados."))