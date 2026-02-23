from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("usuarios/", views.usuario_list, name="usuario_list"),
    path("usuarios/nuevo/", views.usuario_create, name="usuario_create"),
    path("usuarios/<int:pk>/editar/", views.usuario_update, name="usuario_update"),
    path("usuarios/<int:pk>/eliminar/", views.usuario_delete, name="usuario_delete"),
]
