import django_filters
from django.db.models import Q
from .models import Colectivo


class ColectivoFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q", label="Buscar")

    class Meta:
        model = Colectivo
        fields = ["q"]

    def filter_q(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(interno__icontains=value)
            | Q(dominio__icontains=value)
            | Q(marca__icontains=value)
            | Q(modelo__icontains=value)
        )
