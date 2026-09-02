from django.shortcuts import get_object_or_404, render
from .models import Service


def service_list(request):
    services = Service.objects.filter(is_active=True)

    return render(
        request,
        "services/service_list.html",
        {"services": services}
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
        }
    )