from django.contrib import admin
from .models import ProductoImagen


@admin.register(ProductoImagen)
class ProductoImagenAdmin(admin.ModelAdmin):
    list_display = ("producto", "orden", "titulo", "created_at")
    list_filter = ("created_at",)
    search_fields = ("producto__codigo", "producto__nombre", "titulo")