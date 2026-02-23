from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from flota.models import Colectivo


class Command(BaseCommand):
    help = "Crea grupos base y asigna permisos para el sistema (Flota sprint 1)."

    def handle(self, *args, **options):
        ct = ContentType.objects.get_for_model(Colectivo)

        def perm(codename: str):
            return Permission.objects.get(content_type=ct, codename=codename)

        # Permisos estándar del modelo
        p_view = perm("view_colectivo")
        p_add = perm("add_colectivo")
        p_change = perm("change_colectivo")
        p_delete = perm("delete_colectivo")

        # Permisos custom
        p_import = Permission.objects.get(codename="can_import_colectivos", content_type=ct)
        p_export = Permission.objects.get(codename="can_export_colectivos", content_type=ct)

        groups = {
            "Supervisor": [p_view, p_add, p_change, p_delete, p_import, p_export],
            "Taller": [p_view, p_change],
            "Pañol": [p_view, p_import, p_export],
        }

        for name, perms in groups.items():
            g, _ = Group.objects.get_or_create(name=name)
            g.permissions.set(perms)
            g.save()
            self.stdout.write(self.style.SUCCESS(f"Grupo OK: {name} ({len(perms)} permisos)"))

        self.stdout.write(self.style.SUCCESS("Bootstrap de roles completado."))
