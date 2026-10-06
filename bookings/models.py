from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models

from services.models import Service, Specialist


class WorkingHour(models.Model):
    WEEKDAYS = [
        (0, "Понедельник"),
        (1, "Вторник"),
        (2, "Среда"),
        (3, "Четверг"),
        (4, "Пятница"),
        (5, "Суббота"),
        (6, "Воскресенье"),
    ]

    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE,
        related_name="working_hours",
    )

    start_weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAYS,
        verbose_name="С какого дня",
    )

    end_weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAYS,
        verbose_name="По какой день",
    )

    start_time = models.TimeField(
        verbose_name="Начало работы",
    )

    end_time = models.TimeField(
        verbose_name="Конец работы",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно",
    )

    class Meta:
        verbose_name = "Рабочее время"
        verbose_name_plural = "Рабочее время"

    def __str__(self):
        return (
            f"{self.specialist.name} — "
            f"{self.get_start_weekday_display()} - "
            f"{self.get_end_weekday_display()} "
            f"{self.start_time.strftime('%H:%M')} - "
            f"{self.end_time.strftime('%H:%M')}"
        )


class Booking(models.Model):

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    customer_name = models.CharField(
        max_length=100,
    )

    customer_phone = models.CharField(
        max_length=30,
    )

    date = models.DateField()

    time = models.TimeField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    STATUS_CHOICES = [
        ("scheduled", "Запланировано"),
        ("completed", "Завершено"),
        ("cancelled", "Отменено"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
        verbose_name="Статус",
    )

    class Meta:
        verbose_name = "Запись клиента"
        verbose_name_plural = "Записи клиентов"
        ordering = ["-date", "-time"]

        constraints = [
            models.UniqueConstraint(
                fields=["specialist", "date", "time"],
                condition=models.Q(status="scheduled"),
                name="unique_scheduled_specialist_booking",
            ),
        ]

    def clean(self):
        super().clean()

        if self.pk:
            old_booking = Booking.objects.filter(
                pk=self.pk
            ).first()

        if (
                old_booking
                and old_booking.status == "completed"
                and self.status == "cancelled"
            ):
            raise ValidationError(
                    {
                        "status": (
                            "Завершённую запись нельзя отменить."
                        )
                    }
                )
        # Если необходимых данных нет,
        # проверять пересечение невозможно.
        if (
            not self.specialist_id
            or not self.service_id
            or not self.date
            or not self.time
        ):
            return

        # Отменённая запись не блокирует время.
        if self.status != "scheduled":
            return

        # Начало и конец новой записи.
        booking_start = datetime.combine(
            self.date,
            self.time,
        )

        booking_end = booking_start + timedelta(
            minutes=self.service.duration
        )

        # Все активные записи этого специалиста
        # на эту же дату.
        existing_bookings = Booking.objects.filter(
            specialist=self.specialist,
            date=self.date,
            status="scheduled",
        ).exclude(
            pk=self.pk,
        ).select_related("service")

        for booking in existing_bookings:

            existing_start = datetime.combine(
                booking.date,
                booking.time,
            )

            existing_end = existing_start + timedelta(
                minutes=booking.service.duration
            )

            # Проверяем пересечение интервалов.
            if (
                booking_start < existing_end
                and booking_end > existing_start
            ):
                raise ValidationError(
                    {
                        "time": (
                            "Выбранное время пересекается "
                            "с другой записью этого специалиста."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.customer_name} — {self.service.name} — "
            f"{self.date} {self.time}"
        )