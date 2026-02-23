from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("creado el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)

    class Meta:
        abstract = True


class AuditLog(TimeStampedModel):
    """
    Auditoría básica (extensible). Para el módulo Flota por ahora es opcional,
    pero queda listo para crecer.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="usuario",
    )
    action = models.CharField("acción", max_length=80)
    entity = models.CharField("entidad", max_length=80)
    entity_id = models.CharField("id entidad", max_length=80, blank=True)
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    meta = models.JSONField("meta", default=dict, blank=True)

    class Meta:
        verbose_name = "log de auditoría"
        verbose_name_plural = "logs de auditoría"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} - {self.action} - {self.entity}({self.entity_id})"
