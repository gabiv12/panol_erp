from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db.models import Q

from core.permissions import (
    ROLE_ADMIN,
    ROLE_SUPERVISOR,
    ROLE_MECANICO,
    ROLE_CHOFER,
    ROLE_PANOLERO,
    ROLE_ADMINISTRACION,
    role_group_name,
)


def _perms(app_label: str) -> Permission:
    return Permission.objects.filter(content_type__app_label=app_label)


def _perms_prefix(app_label: str, prefixes: list[str]) -> Permission:
    q = Q()
    for p in prefixes:
        q |= Q(codename__startswith=p)
    return _perms(app_label).filter(q)


def _perms_match(app_label: str, patterns: list[str]) -> Permission:
    q = Q()
    for pat in patterns:
        q |= Q(codename__icontains=pat)
    return _perms(app_label).filter(q)


class Command(BaseCommand):
    help = "Inicializa roles (grupos) y permisos base del sistema. Seguro de re-ejecutar."

    def handle(self, *args, **options):
        # Crear grupos
        groups = {
            ROLE_ADMIN: Group.objects.get_or_create(name=role_group_name(ROLE_ADMIN))[0],
            ROLE_SUPERVISOR: Group.objects.get_or_create(name=role_group_name(ROLE_SUPERVISOR))[0],
            ROLE_MECANICO: Group.objects.get_or_create(name=role_group_name(ROLE_MECANICO))[0],
            ROLE_CHOFER: Group.objects.get_or_create(name=role_group_name(ROLE_CHOFER))[0],
            ROLE_PANOLERO: Group.objects.get_or_create(name=role_group_name(ROLE_PANOLERO))[0],
            ROLE_ADMINISTRACION: Group.objects.get_or_create(name=role_group_name(ROLE_ADMINISTRACION))[0],
        }

        # Limpiar permisos actuales de estos grupos (para que sea determinístico)
        for g in groups.values():
            g.permissions.clear()

        # ------------------------------------------------------------
        # GERENCIA (ADMIN): todo lo disponible en flota + inventario + usuarios
        # ------------------------------------------------------------
        admin = groups[ROLE_ADMIN]
        admin.permissions.add(*_perms("flota"))
        admin.permissions.add(*_perms("inventario"))
        admin.permissions.add(*_perms("usuarios"))
        admin.permissions.add(*_perms("core"))

        # ------------------------------------------------------------
        # DIAGRAMADOR / SUPERVISOR
        # - puede operar diagrama (salidas) y ver partes / unidades
        # ------------------------------------------------------------
        diag = groups[ROLE_SUPERVISOR]
        diag.permissions.add(*_perms_prefix("flota", ["view_"]))
        diag.permissions.add(*_perms_prefix("flota", ["add_", "change_"]))
        # Evitar permisos destructivos por defecto
        for p in list(diag.permissions.all()):
            if p.codename.startswith("delete_"):
                diag.permissions.remove(p)

        # ------------------------------------------------------------
        # TALLER / MECANICO
        # - puede gestionar partes
        # ------------------------------------------------------------
        taller = groups[ROLE_MECANICO]
        taller.permissions.add(*_perms_prefix("flota", ["view_"]))
        taller.permissions.add(*_perms_match("flota", ["partediario", "parte"]))
        # Quitar altas/bajas masivas por seguridad
        for p in list(taller.permissions.all()):
            if p.codename.startswith("delete_"):
                taller.permissions.remove(p)

        # ------------------------------------------------------------
        # CHOFER
        # - carga parte desde celular
        # ------------------------------------------------------------
        chofer = groups[ROLE_CHOFER]
        chofer.permissions.add(*_perms_match("flota", ["add_partediario", "view_colectivo", "view_partediario"]))

        # ------------------------------------------------------------
        # PAÑOL / INVENTARIO
        # ------------------------------------------------------------
        panol = groups[ROLE_PANOLERO]
        panol.permissions.add(*_perms_prefix("inventario", ["view_", "add_", "change_"]))
        for p in list(panol.permissions.all()):
            if p.codename.startswith("delete_"):
                panol.permissions.remove(p)

        # ------------------------------------------------------------
        # ADMINISTRACION (cuando se habiliten compras/combustible/reportes)
        # Por ahora: lectura de inventario + lectura flota
        # ------------------------------------------------------------
        adm = groups[ROLE_ADMINISTRACION]
        adm.permissions.add(*_perms_prefix("inventario", ["view_"]))
        adm.permissions.add(*_perms_prefix("flota", ["view_"]))

        self.stdout.write(self.style.SUCCESS("Roles y permisos inicializados."))
        self.stdout.write("Grupos:")
        for k, g in groups.items():
            self.stdout.write(f"- {k} => {g.name} ({g.permissions.count()} perms)")
