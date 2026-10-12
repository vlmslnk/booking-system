from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from bookings.views import get_available_slots
from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id",
            "service",
            "specialist",
            "customer_name",
            "customer_phone",
            "date",
            "time",
            "service_price",
            "service_duration",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "service_price",
            "service_duration",
            "status",
            "created_at",
        ]

    def validate(self, attrs):
        service = attrs["service"]
        specialist = attrs["specialist"]
        selected_date = attrs["date"]
        selected_time = attrs["time"]

        if not service.is_active:
            raise serializers.ValidationError({
                "service": "Услуга неактивна."
            })

        if not specialist.is_active:
            raise serializers.ValidationError({
                "specialist": "Специалист неактивен."
            })

        if not specialist.services.filter(pk=service.pk).exists():
            raise serializers.ValidationError({
                "specialist": "Специалист не оказывает эту услугу."
            })

        available_slots = get_available_slots(
            service, specialist, selected_date
        )

        if selected_time.strftime("%H:%M") not in available_slots:
            raise serializers.ValidationError({
                "time": "Это время недоступно для бронирования."
            })

        return attrs

    def create(self, validated_data):
        booking = Booking(**validated_data)
        try:
            booking.save()
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                getattr(
                    error,
                    "message_dict",
                    {"detail": error.messages},
                )
            )
        return booking
