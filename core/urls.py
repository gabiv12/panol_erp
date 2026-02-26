from django.urls import path
from django.shortcuts import redirect

from . import views

app_name = "core"

urlpatterns = [
    # Home: evita 403 para usuarios sin permisos de flota
    path("", views.home_view, name="home"),

    # Dashboard operativo (no requiere permisos especiales, solo login)
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Alias legacy
    path("bdashboard/", lambda request: redirect("core:dashboard"), name="dashboard_alias"),
]
