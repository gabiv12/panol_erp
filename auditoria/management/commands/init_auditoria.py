from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Asigna permisos de auditoría a GERENCIA (y deja todo listo para usar /auditoria/)."

    def handle(self, *args, **options):
        # Permiso base del modelo
        try:
            perm = Permission.objects.get(codename="view_auditevent")
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR("No existe el permiso view_auditevent. Corré migrate primero."))
            return

        targets = ["GERENCIA"]
        updated = 0
        for name in targets:
            g, _ = Group.objects.get_or_create(name=name)
            if perm not in g.permissions.all():
                g.permissions.add(perm)
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"OK: permisos de auditoría asignados. Grupos actualizados: {updated}"))
        self.stdout.write("Ruta: /auditoria/ (solo usuarios con permiso view_auditevent o superuser).")
