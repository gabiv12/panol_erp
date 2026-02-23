from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission


class Command(BaseCommand):
    help = (
        "Otorga permisos OPERATIVOS de Inventario a un usuario (o a todos los usuarios activos).\n"
        "Incluye: ver catálogos/productos/stock/movimientos + operar movimientos + import/export + manage_stock."
    )

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Usuario al que se le asignan permisos (opcional)")
        parser.add_argument(
            "--all",
            action="store_true",
            help="Si se indica, asigna permisos a TODOS los usuarios activos.",
        )

    def handle(self, *args, **options):
        username = (options.get("username") or "").strip()
        apply_all = bool(options.get("all"))

        if not apply_all and not username:
            self.stderr.write(self.style.ERROR("Debés indicar --username <usuario> o --all"))
            return

        User = get_user_model()

        if apply_all:
            users = list(User.objects.filter(is_active=True))
            if not users:
                self.stderr.write(self.style.ERROR("No hay usuarios activos."))
                return
        else:
            user = User.objects.filter(username=username).first()
            if not user:
                self.stderr.write(self.style.ERROR(f"No existe el usuario: {username}"))
                return
            users = [user]

        # Permisos base (views)
        view_perms = [
            "view_producto",
            "view_stockactual",
            "view_movimientostock",
            "view_categoria",
            "view_subcategoria",
            "view_unidadmedida",
            "view_ubicacion",
            "view_proveedor",
        ]

        # Operación de movimientos (editar / borrar) + administración catálogos (opcional pero útil operativamente)
        crud_perms = [
            "add_categoria", "change_categoria", "delete_categoria",
            "add_subcategoria", "change_subcategoria", "delete_subcategoria",
            "add_unidadmedida", "change_unidadmedida", "delete_unidadmedida",
            "add_ubicacion", "change_ubicacion", "delete_ubicacion",
            "add_proveedor", "change_proveedor", "delete_proveedor",
            "add_producto", "change_producto", "delete_producto",
            "add_movimientostock", "change_movimientostock", "delete_movimientostock",
        ]

        # Custom perms definidos en Producto.Meta.permissions
        custom_perms = [
            "can_manage_stock",
            "can_import_productos",
            "can_export_productos",
        ]

        wanted = set(view_perms + crud_perms + custom_perms)

        perms = Permission.objects.filter(
            content_type__app_label="inventario",
            codename__in=list(wanted),
        )

        perms_by_code = {p.codename: p for p in perms}
        missing = sorted(list(wanted - set(perms_by_code.keys())))

        if missing:
            # No cortamos: si falta alguno por alguna razón, igual asignamos los que existan.
            self.stdout.write(self.style.WARNING(f"Permisos no encontrados (se ignoran): {', '.join(missing)}"))

        total_added = 0
        for u in users:
            before = set(u.user_permissions.values_list("codename", flat=True))
            for code, perm in perms_by_code.items():
                if code not in before:
                    u.user_permissions.add(perm)
                    total_added += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"OK: {u.username} -> ahora tiene view_producto={u.has_perm('inventario.view_producto')} "
                    f"manage_stock={u.has_perm('inventario.can_manage_stock')} "
                    f"change_mov={u.has_perm('inventario.change_movimientostock')}"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"Permisos agregados (total): {total_added}"))