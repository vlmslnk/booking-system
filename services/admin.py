from django.contrib import admin

from .models import PortfolioImage, Service, Specialist


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "duration",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "experience",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )

    filter_horizontal = (
        "services",
    )

@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    list_display = (
        "specialist",
        "title",
        "created_at",
    )

    list_filter = (
        "specialist",
    )

    search_fields = (
        "title",
        "specialist__name",
    )