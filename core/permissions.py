"""Permisos y roles de alto nivel.

Objetivo
--------
El sistema se usa en operación real por perfiles distintos (gerencia, diagramación,
choferes, taller y pañol). Para evitar depender de Django Admin, definimos roles
como **Grupos** de Django y los inicializamos con el comando:

  python manage.py init_roles

Los permisos finos se asignan por grupo, y el UI de "Administración > Usuarios"
permite seleccionar el rol.

Importante
----------
- Superusuario siempre ve todo.
- Los roles son convenciones internas: se pueden ajustar sin migraciones.
"""

from __future__ import annotations

from django.contrib.auth.models import Group
from django.db.models import Q


# Roles históricos (no romper nombres ya usados)
ROLE_ADMIN = "ADMIN"                # equivalencia: Gerencia / Admin principal
ROLE_SUPERVISOR = "SUPERVISOR"      # equivalencia: Diagramador / Coordinación
ROLE_PANOLERO = "PANOLERO"          # equivalencia: Pañol / Inventario
ROLE_MECANICO = "MECANICO"          # equivalencia: Taller
ROLE_CHOFER = "CHOFER"              # equivalencia: Chofer (carga partes)

# Nuevos roles (opcionales)
ROLE_ADMINISTRACION = "ADMINISTRACION"  # compras + reportes + carga administrativa (cuando exista)


ROLE_CHOICES = [
    (ROLE_ADMIN, "Gerencia (acceso total)"),
    (ROLE_SUPERVISOR, "Diagramación / Coordinación"),
    (ROLE_MECANICO, "Taller"),
    (ROLE_CHOFER, "Chofer"),
    (ROLE_PANOLERO, "Pañol / Inventario"),
    (ROLE_ADMINISTRACION, "Administración"),
]


ROLE_GROUPS = {
    ROLE_ADMIN: "GERENCIA",
    ROLE_SUPERVISOR: "DIAGRAMADOR",
    ROLE_MECANICO: "TALLER",
    ROLE_CHOFER: "CHOFERES",
    ROLE_PANOLERO: "PANOL",
    ROLE_ADMINISTRACION: "ADMINISTRACION",
}


def role_group_name(role: str) -> str:
    """Devuelve el nombre del grupo Django asociado a un rol."""
    return ROLE_GROUPS.get(role, ROLE_GROUPS[ROLE_CHOFER])


def _in_group(user, group_name: str) -> bool:
    """True si el usuario pertenece al grupo (o es superuser)."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name=group_name).exists()


# ---------------------------------------------------------------------
# Helpers de compatibilidad (no romper imports viejos)
# ---------------------------------------------------------------------
def is_admin(user) -> bool:
    """Gerencia/Admin. Superuser siempre cuenta como admin."""
    return _in_group(user, ROLE_GROUPS[ROLE_ADMIN])


def is_supervisor(user) -> bool:
    """Diagramador/Coordinación (o Gerencia)."""
    return _in_group(user, ROLE_GROUPS[ROLE_SUPERVISOR]) or is_admin(user)


def is_panoler(user) -> bool:
    """Pañol/Inventario (o Gerencia)."""
    return _in_group(user, ROLE_GROUPS[ROLE_PANOLERO]) or is_admin(user)


def is_taller(user) -> bool:
    """Taller (o Gerencia)."""
    return _in_group(user, ROLE_GROUPS[ROLE_MECANICO]) or is_admin(user)


def is_chofer(user) -> bool:
    """Chofer (o Gerencia/Diagramación)."""
    return _in_group(user, ROLE_GROUPS[ROLE_CHOFER]) or is_supervisor(user)


def set_role_group(user, role: str) -> None:
    """Asigna exactamente 1 rol de los definidos.

    - Remueve el usuario de todos los grupos ROLE_GROUPS
    - Lo agrega al grupo asociado al rol
    """
    if not user:
        return
    target = role_group_name(role)

    role_group_names = list(ROLE_GROUPS.values())
    user.groups.remove(*Group.objects.filter(name__in=role_group_names))

    grp, _ = Group.objects.get_or_create(name=target)
    user.groups.add(grp)


def user_role(user) -> str:
    """Devuelve el rol (clave) si el usuario pertenece a alguno de los grupos.

    Si pertenece a más de uno (no debería), prioriza:
      GERENCIA > DIAGRAMADOR > PANOL > TALLER > CHOFERES > ADMINISTRACION
    """
    if not user or not getattr(user, "is_authenticated", False):
        return ROLE_CHOFER
    if getattr(user, "is_superuser", False):
        return ROLE_ADMIN

    # prioridad manual
    priority = [ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_PANOLERO, ROLE_MECANICO, ROLE_CHOFER, ROLE_ADMINISTRACION]
    for r in priority:
        if user.groups.filter(name=ROLE_GROUPS[r]).exists():
            return r
    return ROLE_CHOFER
