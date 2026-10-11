from django.contrib import admin

from .models import (
    Booking,
    WorkingHour,
    ScheduleException,
    ScheduleExceptionInterval,
)


@admin.register(WorkingHour)
class WorkingHourAdmin(admin.ModelAdmin):
    list_display = (
        "specialist", "start_weekday", "end_weekday",
        "start_time", "end_time", "is_active",
    )
    list_filter = ("specialist", "is_active")
    ordering = ("specialist", "start_weekday", "start_time")


class ScheduleExceptionIntervalInline(admin.TabularInline):
    model = ScheduleExceptionInterval
    extra = 1


@admin.register(ScheduleException)
class ScheduleExceptionAdmin(admin.ModelAdmin):
    list_display = ("specialist", "date", "is_day_off", "note")
    list_filter = ("specialist", "is_day_off", "date")
    search_fields = ("specialist__name", "note")
    inlines = [ScheduleExceptionIntervalInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name", "service", "specialist",
        "date", "time", "status",
    )
    list_filter = ("status", "date", "specialist", "service")
    search_fields = (
        "customer_name", "customer_phone",
        "user__username", "user__email",
    )
    ordering = ("-date", "-time")
    list_per_page = 20
