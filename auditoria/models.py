from __future__ import annotations

from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Registro de acciones a nivel request/response (operación real).

    Diseño:
    - Snapshot de username (por si el usuario cambia o se elimina)
    - Campos cortos para filtros rápidos
    - extra: datos opcionales (ej: querystring relevante)
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    username = models.CharField(max_length=150, blank=True, db_index=True)

    method = models.CharField(max_length=10, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    view_name = models.CharField(max_length=255, blank=True, db_index=True)

    status_code = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    # Categorización simple (útil para reportes futuros)
    app_area = models.CharField(max_length=50, blank=True, db_index=True)  # flota/inventario/usuarios/...
    action = models.CharField(max_length=50, blank=True, db_index=True)  # view/create/update/delete/login/logout

    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Evento de auditoría"
        verbose_name_plural = "Eventos de auditoría"
        indexes = [
            models.Index(fields=["created_at", "username"]),
            models.Index(fields=["created_at", "app_area"]),
        ]

    def __str__(self) -> str:
        u = self.username or (self.user.username if self.user_id else "(sin usuario)")
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {u} {self.method} {self.path}"
