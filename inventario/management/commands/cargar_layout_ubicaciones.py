from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from inventario.models import Ubicacion


class Command(BaseCommand):
    help = (
        "Crea ubicaciones (layout) para un depósito con estructura Pasillo/Módulo/Nivel/Posición. "
        "Genera códigos como: DP-A-01-02-03. "
        "Además crea una ubicación 'SIN-UBICAR' para usar como caja de entrada." 
    )

    def add_arguments(self, parser):
        parser.add_argument("--deposito", required=True, help="Código raíz del depósito (ej: DP)")
        parser.add_argument("--nombre", required=True, help="Nombre del depósito (ej: Depósito Principal)")
        parser.add_argument("--pasillos", required=True, help="Lista de pasillos separada por coma (ej: A,B,C)")
        parser.add_argument("--modulos", type=int, required=True, help="Cantidad de módulos por pasillo (ej: 3)")
        parser.add_argument("--niveles", type=int, required=True, help="Cantidad de niveles por módulo (ej: 4)")
        parser.add_argument("--posiciones", type=int, required=True, help="Cantidad de posiciones por nivel (ej: 5)")

    @transaction.atomic
    def handle(self, *args, **opts):
        dep_code = str(opts["deposito"]).strip().upper()
        dep_name = str(opts["nombre"]).strip()

        pasillos = [p.strip().upper() for p in str(opts["pasillos"]).split(",") if p.strip()]
        modulos = int(opts["modulos"])
        niveles = int(opts["niveles"])
        posiciones = int(opts["posiciones"])

        deposito, _ = Ubicacion.objects.update_or_create(
            codigo=dep_code,
            defaults={
                "nombre": dep_name,
                "tipo": Ubicacion.Tipo.DEPOSITO,
                "padre": None,
                "permite_transferencias": False,
                "is_active": True,
            },
        )

        # Caja de entrada
        Ubicacion.objects.update_or_create(
            codigo=f"{dep_code}-SIN-UBICAR",
            defaults={
                "nombre": f"{dep_name} · Sin ubicar",
                "tipo": Ubicacion.Tipo.POSICION,
                "padre": deposito,
                "pasillo": "SIN",
                "modulo": None,
                "nivel": None,
                "posicion": None,
                "permite_transferencias": True,
                "is_active": True,
            },
        )

        created = 0
        for pas in pasillos:
            pas_obj, _ = Ubicacion.objects.update_or_create(
                codigo=f"{dep_code}-{pas}",
                defaults={
                    "nombre": f"{dep_name} · Pasillo {pas}",
                    "tipo": Ubicacion.Tipo.PASILLO,
                    "padre": deposito,
                    "pasillo": pas,
                    "permite_transferencias": False,
                    "is_active": True,
                },
            )

            for m in range(1, modulos + 1):
                mod_obj, _ = Ubicacion.objects.update_or_create(
                    codigo=f"{dep_code}-{pas}-{m:02d}",
                    defaults={
                        "nombre": f"{dep_name} · {pas} M{m:02d}",
                        "tipo": Ubicacion.Tipo.MODULO,
                        "padre": pas_obj,
                        "pasillo": pas,
                        "modulo": m,
                        "permite_transferencias": False,
                        "is_active": True,
                    },
                )

                for n in range(1, niveles + 1):
                    niv_obj, _ = Ubicacion.objects.update_or_create(
                        codigo=f"{dep_code}-{pas}-{m:02d}-{n:02d}",
                        defaults={
                            "nombre": f"{dep_name} · {pas} M{m:02d} N{n:02d}",
                            "tipo": Ubicacion.Tipo.NIVEL,
                            "padre": mod_obj,
                            "pasillo": pas,
                            "modulo": m,
                            "nivel": n,
                            "permite_transferencias": False,
                            "is_active": True,
                        },
                    )

                    for p in range(1, posiciones + 1):
                        code = f"{dep_code}-{pas}-{m:02d}-{n:02d}-{p:02d}"
                        _, created_flag = Ubicacion.objects.get_or_create(
                            codigo=code,
                            defaults={
                                "nombre": f"{dep_name} · {pas} M{m:02d} N{n:02d} P{p:02d}",
                                "tipo": Ubicacion.Tipo.POSICION,
                                "padre": niv_obj,
                                "pasillo": pas,
                                "modulo": m,
                                "nivel": n,
                                "posicion": p,
                                "permite_transferencias": True,
                                "is_active": True,
                            },
                        )
                        if created_flag:
                            created += 1

        self.stdout.write(self.style.SUCCESS(f"OK: depósito {deposito.codigo} listo. Ubicaciones nuevas: {created}"))
