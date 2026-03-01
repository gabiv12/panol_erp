from django.urls import path
from . import views

app_name = "auditoria"

urlpatterns = [
    path("", views.audit_list, name="audit_list"),
    path("export.csv", views.audit_export_csv, name="audit_export_csv"),
]
