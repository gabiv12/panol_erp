from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from flota.models import Colectivo


class Command(BaseCommand):
    help = "Crea grupos/roles y asigna permisos base (flota por ahora)."

    def handle(self, *args, **options):
        ct = ContentType.objects.get_for_model(Colectivo)

        perms = Permission.objects.filter(content_type=ct)
        perm_map = {p.codename: p for p in perms}

        def get(*codenames):
            return [perm_map[c] for c in codenames if c in perm_map]

        roles = {
            "Chofer": [],  # por ahora solo consulta asignaciones (más adelante)
            "Pañol": [],   # todavía sin inventario
            "Mecánico": [],# todavía sin taller
            "Supervisor": get(
                "view_colectivo",
                "add_colectivo",
                "change_colectivo",
            ),
            "Administrador": get(
                "view_colectivo",
                "add_colectivo",
                "change_colectivo",
                "delete_colectivo",
            ),
        }

        for role, role_perms in roles.items():
            group, _ = Group.objects.get_or_create(name=role)
            if role_perms:
                group.permissions.set(role_perms)
            group.save()

        self.stdout.write(self.style.SUCCESS("Roles creados/actualizados OK."))
        self.stdout.write("Roles: " + ", ".join(roles.keys()))
