from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from auditoria.models import AuditEvent


class Command(BaseCommand):
    help = "Borra eventos de auditoría antiguos (por defecto > 180 días)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=180, help="Conservar últimos N días")

    def handle(self, *args, **options):
        days = int(options.get("days") or 180)
        if days < 7:
            days = 7
        cutoff = timezone.now() - timedelta(days=days)
        qs = AuditEvent.objects.filter(created_at__lt=cutoff)
        n = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"OK: eliminados {n} eventos anteriores a {cutoff:%Y-%m-%d}."))
