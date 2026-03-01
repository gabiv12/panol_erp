from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # Apps
    path("", include("core.urls")),
    path("flota/", include("flota.urls")),
    path("", include("usuarios.urls")),
    path("inventario/", include("inventario.urls")),
    path("auditoria/", include("auditoria.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Favicon (evita 404 en /favicon.ico)
from django.views.generic import RedirectView
from django.templatetags.static import static as static_url

urlpatterns += [
    path("favicon.ico", RedirectView.as_view(url=static_url("img/favicon.ico"), permanent=False)),
    path("apple-touch-icon.png", RedirectView.as_view(url=static_url("img/apple-touch-icon.png"), permanent=False)),
]
