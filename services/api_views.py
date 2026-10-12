
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from .models import Service
from .serializers import ServiceSerializer, SpecialistSerializer


class CatalogPagination(PageNumberPagination):
    page_size = 10


class ServiceListAPIView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    pagination_class = CatalogPagination

    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True)
        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.order_by("id")


class ServiceSpecialistsAPIView(generics.ListAPIView):
    serializer_class = SpecialistSerializer
    pagination_class = CatalogPagination

    def get_queryset(self):
        service = get_object_or_404(
            Service,
            pk=self.kwargs["service_id"],
            is_active=True,
        )

        return service.specialists.filter(
            is_active=True
        ).order_by("id")
