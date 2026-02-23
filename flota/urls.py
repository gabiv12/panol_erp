from django.urls import path
from . import views
from . import partes_views

app_name = "flota"

urlpatterns = [
    path("colectivos/", views.ColectivoListView.as_view(), name="colectivo_list"),
    path("colectivos/nuevo/", views.ColectivoCreateView.as_view(), name="colectivo_create"),
    path("colectivos/<int:pk>/editar/", views.ColectivoUpdateView.as_view(), name="colectivo_update"),
    path("colectivos/<int:pk>/eliminar/", views.ColectivoDeleteView.as_view(), name="colectivo_delete"),

    path("colectivos/<int:pk>/informe/", views.ColectivoReportView.as_view(), name="colectivo_report"),

    path("colectivos/exportar/", views.colectivos_export_csv, name="colectivo_export"),
    path("colectivos/importar/", views.colectivos_import_csv, name="colectivo_import"),
    path("partes/", partes_views.ParteDiarioListView.as_view(), name="parte_list"),
    path("colectivos/<int:colectivo_id>/partes/", partes_views.ParteDiarioListView.as_view(), name="colectivo_parte_list"),
    path("partes/nuevo/", partes_views.ParteDiarioCreateView.as_view(), name="parte_create"),
    path("partes/<int:pk>/", partes_views.ParteDiarioDetailView.as_view(), name="parte_detail"),
    path("partes/<int:pk>/adjuntos/agregar/", partes_views.parte_adjunto_add, name="parte_adjunto_add"),
    path("partes/<int:pk>/adjuntos/<int:adj_id>/eliminar/", partes_views.parte_adjunto_delete, name="parte_adjunto_delete"),


    
]