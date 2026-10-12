
from django.urls import path

from .api_views import ServiceListAPIView, ServiceSpecialistsAPIView

app_name = "services_api"

urlpatterns = [
    path("services/", ServiceListAPIView.as_view(), name="service-list"),
    path(
        "services/<int:service_id>/specialists/",
        ServiceSpecialistsAPIView.as_view(),
        name="service-specialists",
    ),
]
