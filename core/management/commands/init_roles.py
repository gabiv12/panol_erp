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
    MODULE_GROUPS,
    MOD_FLOTA_VIEW,
    MOD_INVENTARIO_VIEW,
    MOD_INVENTARIO_EDIT,
    MOD_TV,
)


def _perms(app_label: str):
    return Permission.objects.filter(content_type__app_label=app_label)


def _perms_prefix(app_label: str, prefixes: list[str]):
    q = Q()
    for p in prefixes:
        q |= Q(codename__startswith=p)
    return _perms(app_label).filter(q)


def _perms_match(app_label: str, patterns: list[str]):
    q = Q()
    for pat in patterns:
        q |= Q(codename__icontains=pat)
    return _perms(app_label).filter(q)


class Command(BaseCommand):
    help = "Inicializa roles (grupos) y permisos base del sistema. Seguro de re-ejecutar."

    def handle(self, *args, **options):
        # Grupos por rol
        groups = {
            ROLE_ADMIN: Group.objects.get_or_create(name=role_group_name(ROLE_ADMIN))[0],
            ROLE_SUPERVISOR: Group.objects.get_or_create(name=role_group_name(ROLE_SUPERVISOR))[0],
            ROLE_MECANICO: Group.objects.get_or_create(name=role_group_name(ROLE_MECANICO))[0],
            ROLE_CHOFER: Group.objects.get_or_create(name=role_group_name(ROLE_CHOFER))[0],
            ROLE_PANOLERO: Group.objects.get_or_create(name=role_group_name(ROLE_PANOLERO))[0],
            ROLE_ADMINISTRACION: Group.objects.get_or_create(name=role_group_name(ROLE_ADMINISTRACION))[0],
        }

        # Grupos por módulo (accesos extra)
        mod_groups = {k: Group.objects.get_or_create(name=gname)[0] for k, gname in MODULE_GROUPS.items()}

        # Limpiar permisos actuales (determinístico)
        for g in list(groups.values()) + list(mod_groups.values()):
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
        # ------------------------------------------------------------
        diag = groups[ROLE_SUPERVISOR]
        diag.permissions.add(*_perms_prefix("flota", ["view_"]))
        diag.permissions.add(*_perms_prefix("flota", ["add_", "change_"]))
        for p in list(diag.permissions.all()):
            if p.codename.startswith("delete_"):
                diag.permissions.remove(p)

        # ------------------------------------------------------------
        # TALLER / MECANICO
        # ------------------------------------------------------------
        taller = groups[ROLE_MECANICO]
        taller.permissions.add(*_perms_prefix("flota", ["view_"]))
        taller.permissions.add(*_perms_match("flota", ["partediario", "parte", "change_partediario"]))
        for p in list(taller.permissions.all()):
            if p.codename.startswith("delete_"):
                taller.permissions.remove(p)

        # ------------------------------------------------------------
        # CHOFER
        # - solo: crear parte chofer + ver diagrama (salidas)
        # ------------------------------------------------------------
        chofer = groups[ROLE_CHOFER]
        chofer.permissions.add(*_perms_match("flota", ["add_partediario", "view_salidaprogramada"]))
        # No dar view_partediario para no habilitar listados internos

        # ------------------------------------------------------------
        # PAÑOL / INVENTARIO
        # ------------------------------------------------------------
        panol = groups[ROLE_PANOLERO]
        panol.permissions.add(*_perms_prefix("inventario", ["view_", "add_", "change_"]))
        for p in list(panol.permissions.all()):
            if p.codename.startswith("delete_"):
                panol.permissions.remove(p)

        # ------------------------------------------------------------
        # ADMINISTRACION / PROVEEDORES (carga ingresos)
        # - puede: alta/edición inventario + proveedores + movimientos (sin delete)
        # ------------------------------------------------------------
        adm = groups[ROLE_ADMINISTRACION]
        adm.permissions.add(*_perms_prefix("inventario", ["view_", "add_", "change_"]))
        for p in list(adm.permissions.all()):
            if p.codename.startswith("delete_"):
                adm.permissions.remove(p)

        # ------------------------------------------------------------
        # MÓDULOS (accesos extra)
        # ------------------------------------------------------------
        # Flota lectura
        g = mod_groups[MOD_FLOTA_VIEW]
        g.permissions.add(*_perms_prefix("flota", ["view_"]))

        # Inventario lectura
        g = mod_groups[MOD_INVENTARIO_VIEW]
        g.permissions.add(*_perms_prefix("inventario", ["view_"]))

        # Inventario carga (sin delete)
        g = mod_groups[MOD_INVENTARIO_EDIT]
        g.permissions.add(*_perms_prefix("inventario", ["view_", "add_", "change_"]))
        for p in list(g.permissions.all()):
            if p.codename.startswith("delete_"):
                g.permissions.remove(p)

        # TV (requiere ver salidas y partes para armar pantallas)
        g = mod_groups[MOD_TV]
        g.permissions.add(*_perms_match("flota", ["view_salidaprogramada", "view_partediario", "view_colectivo"]))

        self.stdout.write(self.style.SUCCESS("Roles y permisos inicializados."))
        self.stdout.write("Grupos (roles):")
        for k, g in groups.items():
            self.stdout.write(f"- {k} => {g.name} ({g.permissions.count()} perms)")
        self.stdout.write("Grupos (módulos):")
        for k, g in mod_groups.items():
            self.stdout.write(f"- {k} => {g.name} ({g.permissions.count()} perms)")
