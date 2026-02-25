from django.urls import path

from . import partes_views
from . import salidas_views
from . import informe_views
from . import views

app_name = "flota"

urlpatterns = [
    # Colectivos
    path("colectivos/", views.ColectivoListView.as_view(), name="colectivo_list"),
    path("colectivos/nuevo/", views.ColectivoCreateView.as_view(), name="colectivo_create"),
    path("colectivos/<int:pk>/editar/", views.ColectivoUpdateView.as_view(), name="colectivo_update"),
    path("colectivos/<int:pk>/eliminar/", views.ColectivoDeleteView.as_view(), name="colectivo_delete"),
    path("colectivos/<int:pk>/informe/", views.ColectivoReportView.as_view(), name="colectivo_report"),
    path("colectivos/exportar/", views.colectivos_export_csv, name="colectivo_export"),
    path("colectivos/importar/", views.colectivos_import_csv, name="colectivo_import"),

    # Informe flota (operativo)
    path("informe/", informe_views.informe_flota, name="informe_flota"),

    # Partes diarios
    path("partes/", partes_views.ParteDiarioListView.as_view(), name="parte_list"),
    path("colectivos/<int:colectivo_id>/partes/", partes_views.ParteDiarioListView.as_view(), name="colectivo_parte_list"),
    path("partes/nuevo/", partes_views.ParteDiarioCreateView.as_view(), name="parte_create"),
    path("partes/<int:pk>/", partes_views.ParteDiarioDetailView.as_view(), name="parte_detail"),
    path("partes/<int:pk>/adjuntos/agregar/", partes_views.parte_adjunto_add, name="parte_adjunto_add"),
    path("partes/<int:pk>/adjuntos/<int:adj_id>/eliminar/", partes_views.parte_adjunto_delete, name="parte_adjunto_delete"),

    # Horarios / Diagrama
    path("salidas/", salidas_views.SalidaProgramadaListView.as_view(), name="salida_list"),
    path("salidas/nuevo/", salidas_views.SalidaProgramadaCreateView.as_view(), name="salida_create"),
    path("salidas/<int:pk>/editar/", salidas_views.SalidaProgramadaUpdateView.as_view(), name="salida_update"),
    path("salidas/<int:pk>/eliminar/", salidas_views.SalidaProgramadaDeleteView.as_view(), name="salida_delete"),
    path("salidas/diagrama/", salidas_views.diagrama_print, name="salida_diagrama_print"),
    path("salidas/diagrama/editar/", salidas_views.diagrama_edit, name="salida_diagrama_edit"),
    path("salidas/copiar-dia-anterior/", salidas_views.salidas_copiar_dia_anterior, name="salida_copy_prev_day"),
    path("salidas/copiar-15-dias/", salidas_views.salidas_copiar_15_dias, name="salida_copy_15"),
    path("plan/", salidas_views.plan_15_dias, name="plan_15"),
    path("plan/print/", salidas_views.plan_15_print, name="plan_15_print"),
    path("plan/export.csv", salidas_views.plan_15_export_csv, name="plan_15_export_csv"),
    path("plan/copiar-quincena/", salidas_views.plan_15_copiar_quincena_anterior, name="plan_15_copiar_quincena_anterior"),

    # API
    path("api/colectivo-info/", salidas_views.api_colectivo_info, name="api_colectivo_info"),

    # Pantalla TV
    path("tv/horarios/", salidas_views.tv_horarios, name="tv_horarios"),
    path("tv/taller/", partes_views.tv_taller, name="tv_taller"),
]
