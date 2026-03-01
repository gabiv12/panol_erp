from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "username", "method", "path", "status_code", "duration_ms", "app_area", "action")
    list_filter = ("app_area", "action", "method", "status_code")
    search_fields = ("username", "path", "view_name", "user_agent")
    ordering = ("-created_at",)
