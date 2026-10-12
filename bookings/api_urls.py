
from django.urls import path

from .api_views import (
    MyBookingsAPIView,
    BookingDetailAPIView,
    CancelMyBookingAPIView,
)

app_name = "bookings_api"

urlpatterns = [
    path("bookings/", MyBookingsAPIView.as_view(), name="my-bookings"),
    path("bookings/<int:pk>/", BookingDetailAPIView.as_view(), name="booking-detail"),
    path("bookings/<int:pk>/cancel/", CancelMyBookingAPIView.as_view(), name="booking-cancel"),
]
