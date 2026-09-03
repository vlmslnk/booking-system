from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.service_list,
        name="service_list"
    ),

    path(
        "specialists/",
        views.specialist_list,
        name="specialist_list"
    ),

    path(
        "specialists/<int:specialist_id>/",
        views.specialist_detail,
        name="specialist_detail"
    ),

    path(
        "<int:service_id>/",
        views.service_detail,
        name="service_detail"
    ),
]