from django.shortcuts import get_object_or_404, render

from .models import Service, Specialist


def service_list(request):
    services = Service.objects.filter(
        is_active=True
    )

    return render(
        request,
        "services/service_list.html",
        {
            "services": services,
        },
    )


def service_detail(request, service_id):
    service = get_object_or_404(
        Service,
        id=service_id,
        is_active=True
    )

    specialists = service.specialists.filter(
        is_active=True
    )

    return render(
        request,
        "services/service_detail.html",
        {
            "service": service,
            "specialists": specialists,
        },
    )


def specialist_list(request):
    specialists = Specialist.objects.filter(
        is_active=True
    ).prefetch_related("services")

    return render(
        request,
        "services/specialist_list.html",
        {
            "specialists": specialists,
        },
    )


def specialist_detail(request, specialist_id):
    specialist = get_object_or_404(
        Specialist,
        id=specialist_id,
        is_active=True
    )

    services = specialist.services.filter(
        is_active=True
    )

    return render(
        request,
        "services/specialist_detail.html",
        {
            "specialist": specialist,
            "services": services,
        },
    )

def home(request):
    return render(request, "home/home.html")