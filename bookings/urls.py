from django.urls import path

from . import views


urlpatterns = [
    path(
        "create/<int:service_id>/<int:specialist_id>/",
        views.create_booking,
        name="create_booking",
    ),
    path(
        "success/<int:booking_id>/",
        views.booking_success,
        name="booking_success",
    ),
    path(
        "cancel/<int:booking_id>/",
        views.cancel_booking,
        name="cancel_booking",
    ),
]