from django.contrib import admin
from .models import Service, Specialist


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)