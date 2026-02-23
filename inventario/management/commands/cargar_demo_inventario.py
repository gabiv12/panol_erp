from __future__ import annotations

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.contrib.auth.models import Permission
from django.utils import timezone

from inventario.models import (
    Categoria,
    Subcategoria,
    UnidadMedida,
    Proveedor,
    Ubicacion,
    Producto,
    StockActual,
    MovimientoStock,
)


DEMO_PREFIX = "DEMO-"  # evita colisiones con tus códigos reales


def upsert_stock(producto: Producto, ubicacion: Ubicacion, cantidad: Decimal) -> StockActual:
    """
    Upsert robusto (evita el bug que viste con update_or_create + UNIQUE):
    1) intenta UPDATE
    2) si no actualizó, intenta INSERT
    3) si choca por UNIQUE, hace UPDATE y listo
    """
    mgr = StockActual._base_manager
    updated = mgr.filter(producto=producto, ubicacion=ubicacion).update(
        cantidad=cantidad,
        last_movement_at=timezone.now(),
    )
    if updated:
        return mgr.get(producto=producto, ubicacion=ubicacion)

    try:
        return mgr.create(
            producto=producto,
            ubicacion=ubicacion,
            cantidad=cantidad,
            last_movement_at=timezone.now(),
        )
    except IntegrityError:
        # ya existía (pero por algún motivo no matcheó en el primer get)
        mgr.filter(producto=producto, ubicacion=ubicacion).update(
            cantidad=cantidad,
            last_movement_at=timezone.now(),
        )
        return mgr.get(producto=producto, ubicacion=ubicacion)


class Command(BaseCommand):
    help = "Carga DEMO en Inventario (catálogos, productos, stock, movimientos). Seguro e idempotente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-demo",
            action="store_true",
            help="Borra SOLO registros DEMO (códigos que empiezan con DEMO-) antes de cargar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset = options.get("reset_demo", False)

        # Usuario demo
        User = get_user_model()
        demo_user, _ = User.objects.get_or_create(
            username="demo",
            defaults={"is_staff": True, "is_active": True},
        )
        if not demo_user.has_usable_password():
            demo_user.set_password("demo1234")
            demo_user.save(update_fields=["password"])

        # Permisos (para que el usuario demo pueda entrar a Inventario)
        # Otorga TODOS los permisos del app "inventario".
        inv_perms = Permission.objects.filter(content_type__app_label="inventario")
        if inv_perms.exists():
            demo_user.user_permissions.add(*inv_perms)

        if reset:
            # borrar stock y movimientos vinculados a productos DEMO
            demo_products = Producto.objects.filter(codigo__startswith=DEMO_PREFIX)
            StockActual.objects.filter(producto__in=demo_products).delete()
            MovimientoStock.objects.filter(producto__in=demo_products).delete()
            demo_products.delete()

        # Catálogos base (no se borran en reset: pueden ser reutilizados por datos reales)
        cat_rep, _ = Categoria.objects.get_or_create(nombre="Repuestos", defaults={"is_active": True})
        cat_lub, _ = Categoria.objects.get_or_create(nombre="Lubricantes", defaults={"is_active": True})
        cat_seg, _ = Categoria.objects.get_or_create(nombre="Seguridad", defaults={"is_active": True})

        sub_fil, _ = Subcategoria.objects.get_or_create(categoria=cat_rep, nombre="Filtros", defaults={"is_active": True})
        sub_fre, _ = Subcategoria.objects.get_or_create(categoria=cat_rep, nombre="Frenos", defaults={"is_active": True})
        sub_ace, _ = Subcategoria.objects.get_or_create(categoria=cat_lub, nombre="Aceites", defaults={"is_active": True})
        sub_epp, _ = Subcategoria.objects.get_or_create(categoria=cat_seg, nombre="EPP", defaults={"is_active": True})

        um_u, _ = UnidadMedida.objects.get_or_create(abreviatura="u", defaults={"nombre": "Unidad", "is_active": True})
        um_lt, _ = UnidadMedida.objects.get_or_create(abreviatura="lt", defaults={"nombre": "Litro", "is_active": True})
        um_cj, _ = UnidadMedida.objects.get_or_create(abreviatura="caja", defaults={"nombre": "Caja", "is_active": True})

        prov_a, _ = Proveedor.objects.get_or_create(nombre="Proveedor A", defaults={"is_active": True})
        prov_b, _ = Proveedor.objects.get_or_create(nombre="Proveedor B", defaults={"is_active": True})

        ub_dep, _ = Ubicacion.objects.get_or_create(codigo="DEP-01", defaults={"nombre": "Depósito Central", "is_active": True})
        ub_tal, _ = Ubicacion.objects.get_or_create(codigo="TAL-01", defaults={"nombre": "Taller", "is_active": True})
        ub_mos, _ = Ubicacion.objects.get_or_create(codigo="MOS-01", defaults={"nombre": "Mostrador", "is_active": True})

        # Productos DEMO
        demo_rows = [
            ("REP-0001", "Filtro de aceite", "Filtro estándar motor", cat_rep, sub_fil, um_u, prov_a, Decimal("2"), False),
            ("REP-0002", "Pastillas de freno", "Juego delantero", cat_rep, sub_fre, um_u, prov_b, Decimal("4"), False),
            ("LUB-0001", "Aceite 15W40 (4L)", "Lubricante diesel", cat_lub, sub_ace, um_lt, prov_a, Decimal("10"), False),
            ("SEG-0001", "Guantes de nitrilo", "Caja x100", cat_seg, sub_epp, um_cj, prov_b, Decimal("1"), False),
        ]

        created = 0
        for code, nombre, desc, cat, sub, um, prov, stock_min, venc in demo_rows:
            codigo = f"{DEMO_PREFIX}{code}"
            p, is_new = Producto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "descripcion": desc,
                    "categoria": cat,
                    "subcategoria": sub,
                    "unidad_medida": um,
                    "proveedor": prov,
                    "stock_minimo": stock_min,
                    "maneja_vencimiento": venc,
                    "is_active": True,
                },
            )
            if not is_new:
                # si ya existía, lo actualizamos para que se vea coherente
                Producto.objects.filter(pk=p.pk).update(
                    nombre=nombre,
                    descripcion=desc,
                    categoria=cat,
                    subcategoria=sub,
                    unidad_medida=um,
                    proveedor=prov,
                    stock_minimo=stock_min,
                    maneja_vencimiento=venc,
                    is_active=True,
                )
            created += 1

            # Stock por ubicación (upsert robusto)
            upsert_stock(p, ub_dep, Decimal("25"))
            upsert_stock(p, ub_tal, Decimal("7"))
            upsert_stock(p, ub_mos, Decimal("2"))

            # Movimientos DEMO simples
            MovimientoStock.objects.create(
                producto=p,
                ubicacion=ub_dep,
                tipo=MovimientoStock.Tipo.INGRESO,
                cantidad=Decimal("10"),
                proveedor=prov,
                referencia="Carga DEMO",
                observaciones="Movimiento demo (ingreso)",
                usuario=demo_user,
            )

        self.stdout.write(self.style.SUCCESS(f"✅ Demo cargado: {created} productos. Usuario demo: demo / demo1234"))
        self.stdout.write(self.style.SUCCESS("👉 Probá: Inventario > Productos / Stock / Movimientos / Configuración"))
