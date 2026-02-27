from __future__ import annotations

from typing import Dict, Any

from core.permissions import (
    ROLE_GROUPS,
    ROLE_ADMIN,
    ROLE_SUPERVISOR,
    ROLE_MECANICO,
    ROLE_CHOFER,
    ROLE_PANOLERO,
    ROLE_ADMINISTRACION,
    MODULE_GROUPS,
    MOD_FLOTA_VIEW,
    MOD_INVENTARIO_VIEW,
    MOD_INVENTARIO_EDIT,
    MOD_TV,
)


def _in_group(user, group_name: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name=group_name).exists()


def _in_any(user, names: list[str]) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name__in=names).exists()


def nav_visibility(request) -> Dict[str, Any]:
    """
    Flags para templates (sidebar).
    Compat:
      - nav_visibility
      - nav_flags (alias)
    """
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {}

    if getattr(user, "is_superuser", False):
        return {
            "show_flota": True,
            "show_flota_full": True,
            "show_inventario": True,
            "show_admin": True,
            "show_tv": True,
            "show_proximamente": True,
            "is_chofer_only": False,
        }

    # Roles
    is_gerencia = _in_group(user, ROLE_GROUPS[ROLE_ADMIN])
    is_diagramador = _in_group(user, ROLE_GROUPS[ROLE_SUPERVISOR])
    is_taller = _in_group(user, ROLE_GROUPS[ROLE_MECANICO])
    is_panoler = _in_group(user, ROLE_GROUPS[ROLE_PANOLERO])
    is_administra = _in_group(user, ROLE_GROUPS[ROLE_ADMINISTRACION])
    is_chofer = _in_group(user, ROLE_GROUPS[ROLE_CHOFER])

    # Módulos (accesos extra)
    mod_flota = _in_group(user, MODULE_GROUPS[MOD_FLOTA_VIEW])
    mod_inv_view = _in_group(user, MODULE_GROUPS[MOD_INVENTARIO_VIEW]) or _in_group(user, MODULE_GROUPS[MOD_INVENTARIO_EDIT])
    mod_tv = _in_group(user, MODULE_GROUPS[MOD_TV])

    # Chofer puro: solo chofer, sin otros roles ni accesos extra.
    is_chofer_only = bool(is_chofer and not (is_gerencia or is_diagramador or is_taller or is_panoler or is_administra or mod_flota or mod_inv_view or mod_tv))

    show_flota = bool(is_gerencia or is_diagramador or is_taller or is_chofer_only or mod_flota)
    show_flota_full = bool(is_gerencia or is_diagramador or is_taller)

    show_inventario = bool(is_gerencia or is_panoler or is_administra or mod_inv_view)
    show_admin = bool(is_gerencia)
    show_tv = bool(is_gerencia or is_diagramador or is_taller or mod_tv)
    show_proximamente = bool(is_gerencia)

    return {
        "show_flota": show_flota,
        "show_flota_full": show_flota_full,
        "show_inventario": show_inventario,
        "show_admin": show_admin,
        "show_tv": show_tv,
        "show_proximamente": show_proximamente,
        "is_chofer_only": is_chofer_only,
    }


def nav_flags(request) -> Dict[str, Any]:
    return nav_visibility(request)
