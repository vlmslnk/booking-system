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
        ordering = ["-date", "-time"]

        constraints = [
            models.UniqueConstraint(
                fields=["specialist", "date", "time"],
                name="unique_specialist_booking",
            ),
        ]

    def __str__(self):
        return (
            f"{self.customer_name} — {self.service.name} — "
            f"{self.date} {self.time}"
        )