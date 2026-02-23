from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Colectivo
from .resources import ColectivoResource


@admin.register(Colectivo)
class ColectivoAdmin(ImportExportModelAdmin):
    resource_class = ColectivoResource
    list_display = ("interno", "dominio", "marca", "modelo", "anio_modelo")
    search_fields = ("interno", "dominio", "marca", "modelo")
