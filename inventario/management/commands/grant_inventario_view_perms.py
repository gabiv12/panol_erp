from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission


class Command(BaseCommand):
    help = "Otorga permisos VIEW de inventario a un usuario (para demo / presentación)."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Usuario al que se le asignan permisos")

    def handle(self, *args, **options):
        username = options["username"]
        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if not user:
            self.stderr.write(self.style.ERROR(f"No existe el usuario: {username}"))
            return

        perms = [
            'view_producto',
            'view_stockactual',
            'view_movimientostock',
            'view_categoria',
            'view_subcategoria',
            'view_unidadmedida',
            'view_ubicacion',
            'view_proveedor',
        ]

        added = 0
        for codename in perms:
            perm = Permission.objects.filter(content_type__app_label='inventario', codename=codename).first()
            if not perm:
                continue
            user.user_permissions.add(perm)
            added += 1

        self.stdout.write(self.style.SUCCESS(f"OK: {username} -> permisos inventario agregados: {added}"))
