from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from core.permissions import ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_PANOLERO, ROLE_MECANICO, ROLE_CHOFER
from flota.models import Colectivo


class Command(BaseCommand):
    help = "Crea grupos/roles y asigna permisos básicos (especialmente Flota)."

    def handle(self, *args, **options):
        roles = [ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_PANOLERO, ROLE_MECANICO, ROLE_CHOFER]
        groups = {}
        for r in roles:
            g, _ = Group.objects.get_or_create(name=r)
            groups[r] = g

        # Permisos del modelo Colectivo
        ct = ContentType.objects.get_for_model(Colectivo)
        perms = Permission.objects.filter(content_type=ct)
        perm_map = {p.codename: p for p in perms}

        # Codenames típicos: add_colectivo, change_colectivo, delete_colectivo, view_colectivo
        add_p = perm_map.get("add_colectivo")
        change_p = perm_map.get("change_colectivo")
        delete_p = perm_map.get("delete_colectivo")
        view_p = perm_map.get("view_colectivo")

        # ADMIN: todos
        for p in [add_p, change_p, delete_p, view_p]:
            if p:
                groups[ROLE_ADMIN].permissions.add(p)

        # SUPERVISOR: add/change/view (sin delete por seguridad)
        for p in [add_p, change_p, view_p]:
            if p:
                groups[ROLE_SUPERVISOR].permissions.add(p)

        # PANOLERO / MECANICO / CHOFER: solo view
        for role in [ROLE_PANOLERO, ROLE_MECANICO, ROLE_CHOFER]:
            if view_p:
                groups[role].permissions.add(view_p)

        self.stdout.write(self.style.SUCCESS("Roles creados y permisos asignados correctamente."))
        self.stdout.write("Roles: ADMIN, SUPERVISOR, PANOLERO, MECANICO, CHOFER")
