from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Colectivo, SalidaProgramada
from .choferes_models import Chofer
from .resources import ColectivoResource


@admin.register(Colectivo)
class ColectivoAdmin(ImportExportModelAdmin):
    resource_class = ColectivoResource
    list_display = ("interno", "dominio", "marca", "modelo", "anio_modelo")
    search_fields = ("interno", "dominio", "marca", "modelo")



@admin.register(SalidaProgramada)
class SalidaProgramadaAdmin(admin.ModelAdmin):
    list_display = ("salida_programada", "colectivo", "tipo", "estado", "chofer")
    list_filter = ("tipo", "estado")
    search_fields = ("colectivo__dominio", "colectivo__interno", "chofer", "recorrido", "nota")
    ordering = ("-salida_programada",)


@admin.register(Chofer)
class ChoferAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'legajo', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('apellido', 'nombre', 'legajo')

