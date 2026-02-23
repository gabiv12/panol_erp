from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from flota.models import Colectivo


class Command(BaseCommand):
    help = "Otorga permisos de Flota (ver colectivos + opcionales import/export) a un usuario."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)
        parser.add_argument("--full", action="store_true", help="También otorga add/change/delete + import/export si existen.")

    def handle(self, *args, **opts):
        username = opts["username"]
        full = bool(opts["full"])

        User = get_user_model()
        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(f"No existe el usuario: {username}")
            return

        ct = ContentType.objects.get_for_model(Colectivo)

        # Permisos base (view)
        perms = []
        view_perm = Permission.objects.filter(content_type=ct, codename="view_colectivo").first()
        if view_perm:
            perms.append(view_perm)

        # Opcionales (si tu modelo los define)
        maybe = ["can_export_colectivos", "can_import_colectivos"]
        for codename in maybe:
            p = Permission.objects.filter(content_type=ct, codename=codename).first()
            if p:
                perms.append(p)

        if full:
            for codename in ["add_colectivo", "change_colectivo", "delete_colectivo"]:
                p = Permission.objects.filter(content_type=ct, codename=codename).first()
                if p:
                    perms.append(p)

        if not perms:
            self.stderr.write("No encontré permisos para asignar (revisar codenames en flota).")
            return

        u.user_permissions.add(*perms)
        self.stdout.write(f"Permisos asignados a {username}: {[p.codename for p in perms]}")