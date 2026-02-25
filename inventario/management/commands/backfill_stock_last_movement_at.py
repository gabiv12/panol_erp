from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from inventario.models import StockActual


class Command(BaseCommand):
    help = "Normaliza StockActual.last_movement_at para que sea timezone-aware y no genere warnings."

    def handle(self, *args, **options):
        tz = timezone.get_current_timezone()

        updated = 0
        qs = StockActual.objects.all().only("id", "last_movement_at", "created_at", "updated_at")
        for st in qs.iterator():
            dt = st.last_movement_at

            if dt is None:
                dt_new = st.updated_at or st.created_at or timezone.now()
            elif timezone.is_naive(dt):
                # Interpretamos el valor como horario local del sistema
                dt_new = timezone.make_aware(dt, tz)
            else:
                continue

            StockActual.objects.filter(pk=st.pk).update(last_movement_at=dt_new)
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"OK: {updated} filas actualizadas."))
