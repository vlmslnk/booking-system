from datetime import datetime, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from bookings.api_exceptions import SlotUnavailable
from bookings.views import get_available_slots
from services.models import Specialist
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

    def _slot_is_occupied(self, service, specialist, selected_date, selected_time):
        start = datetime.combine(selected_date, selected_time)
        end = start + timedelta(minutes=service.duration)

        bookings = Booking.objects.filter(
            specialist=specialist,
            date=selected_date,
            status="scheduled",
        ).select_related("service")

        for booking in bookings:
            existing_start = datetime.combine(booking.date, booking.time)
            duration = booking.service_duration or booking.service.duration
            existing_end = existing_start + timedelta(minutes=duration)

            if start < existing_end and end > existing_start:
                return True

        return False

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
            if self._slot_is_occupied(
                service, specialist, selected_date, selected_time
            ):
                raise SlotUnavailable()

            raise serializers.ValidationError({
                "time": "Это время недоступно для бронирования."
            })

        return attrs

    def create(self, validated_data):
        service = validated_data["service"]
        specialist = validated_data["specialist"]
        selected_date = validated_data["date"]
        selected_time = validated_data["time"]

        try:
            with transaction.atomic():
                Specialist.objects.select_for_update().get(pk=specialist.pk)

                available_slots = get_available_slots(
                    service, specialist, selected_date
                )

                if selected_time.strftime("%H:%M") not in available_slots:
                    if self._slot_is_occupied(
                        service, specialist, selected_date, selected_time
                    ):
                        raise SlotUnavailable()

                    raise serializers.ValidationError({
                        "time": "Это время недоступно для бронирования."
                    })

                booking = Booking(**validated_data)

                try:
                    booking.save()
                except DjangoValidationError as error:
                    messages = getattr(error, "message_dict", {})
                    time_errors = messages.get("time", [])

                    if any("пересекается" in str(message) for message in time_errors):
                        raise SlotUnavailable() from error

                    raise serializers.ValidationError(
                        messages or {"detail": error.messages}
                    ) from error

                return booking

        except IntegrityError as error:
            raise SlotUnavailable() from error
