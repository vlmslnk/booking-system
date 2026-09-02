from django.contrib import admin

from .models import Booking, WorkingHour


@admin.register(WorkingHour)
class WorkingHourAdmin(admin.ModelAdmin):
    list_display = (
        "specialist",
        "start_weekday",
        "end_weekday",
        "start_time",
        "end_time",
        "is_active",
    )

    list_filter = (
        "specialist",
        "is_active",
    )

    search_fields = (
        "specialist__name",
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "service",
        "specialist",
        "date",
        "time",
    )

    list_filter = (
        "date",
        "specialist",
        "service",
    )

    search_fields = (
        "customer_name",
        "customer_phone",
    )

    ordering = (
        "-date",
        "-time",
    )