
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Booking
from .api_serializers import BookingSerializer


class MyBookingsAPIView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related("service", "specialist")

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except DjangoValidationError as error:
            raise ValidationError(
                getattr(error, "message_dict", {"detail": error.messages})
            )


class BookingDetailAPIView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related("service", "specialist")


class CancelMyBookingAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = get_object_or_404(
            Booking,
            pk=pk,
            user=request.user,
        )

        if booking.status == "completed":
            return Response(
                {"detail": "Завершённую запись нельзя отменить."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.status == "cancelled":
            return Response(
                {"detail": "Запись уже отменена."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "cancelled"
        booking.save()

        return Response(
            {"detail": "Запись отменена."},
            status=status.HTTP_200_OK,
        )
