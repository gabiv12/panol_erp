from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

from core.permissions import ROLE_CHOFER, role_group_name


class Command(BaseCommand):
    help = "Ajusta permisos del grupo CHOFERES para que no pueda entrar a pantallas internas (evita 403 por navegación)."

    def handle(self, *args, **options):
        group_name = role_group_name(ROLE_CHOFER)
        g, _ = Group.objects.get_or_create(name=group_name)

        # En producción real, el chofer solo necesita:
        # - Cargar parte (flujo chofer)
        # - Ver diagrama/horarios
        allowed_flota = {"add_partediario", "view_salidaprogramada"}

        flota_perms = Permission.objects.filter(content_type__app_label="flota")
        removed = 0
        for p in flota_perms:
            if p.codename not in allowed_flota and g.permissions.filter(pk=p.pk).exists():
                g.permissions.remove(p)
                removed += 1

        added = 0
        for p in flota_perms.filter(codename__in=allowed_flota):
            if not g.permissions.filter(pk=p.pk).exists():
                g.permissions.add(p)
                added += 1

        self.stdout.write(self.style.SUCCESS(f"CHOFERES actualizado: +{added} / -{removed}."))
