from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "core"

urlpatterns = [
    path("", lambda request: redirect("flota:colectivo_list"), name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("bdashboard/", lambda request: redirect("core:dashboard"), name="dashboard_alias"),
]