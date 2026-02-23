ROLE_ADMIN = "ADMIN"
ROLE_SUPERVISOR = "SUPERVISOR"
ROLE_PANOLERO = "PANOLERO"
ROLE_MECANICO = "MECANICO"
ROLE_CHOFER = "CHOFER"

ALL_ROLES = [ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_PANOLERO, ROLE_MECANICO, ROLE_CHOFER]


def is_admin(user) -> bool:
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=ROLE_ADMIN).exists())


def is_supervisor(user) -> bool:
    return user.is_authenticated and user.groups.filter(name=ROLE_SUPERVISOR).exists()


def can_manage_flota(user) -> bool:
    # Admin o Supervisor gestionan Flota
    return is_admin(user) or is_supervisor(user)


def can_view_flota(user) -> bool:
    # Todos los roles autenticados pueden ver flota
    return user.is_authenticated
