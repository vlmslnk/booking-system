from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

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

    def clean(self):
        super().clean()

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    "end_time": (
                        "Время окончания должно быть позже "
                        "времени начала."
                    )
                })

        if (
            self.start_weekday is not None
            and self.end_weekday is not None
            and self.start_weekday > self.end_weekday
        ):
            raise ValidationError({
                "end_weekday": (
                    "Последний день не может быть раньше "
                    "первого дня."
                )
            })

    def __str__(self):
        return (
            f"{self.specialist.name} — "
            f"{self.get_start_weekday_display()} - "
            f"{self.get_end_weekday_display()} "
            f"{self.start_time.strftime('%H:%M')} - "
            f"{self.end_time.strftime('%H:%M')}"
        )


class Booking(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Запланировано"),
        ("completed", "Завершено"),
        ("cancelled", "Отменено"),
    ]

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.PROTECT,
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

    service_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена на момент записи",
    )

    service_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Длительность на момент записи",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

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

        old_booking = None
        if self.pk:
            old_booking = Booking.objects.filter(pk=self.pk).first()

        if (
            old_booking
            and old_booking.status == "completed"
            and self.status == "cancelled"
        ):
            raise ValidationError({
                "status": "Завершённую запись нельзя отменить."
            })

        if (
            not self.specialist_id
            or not self.service_id
            or not self.date
            or not self.time
        ):
            return

        if self.status != "scheduled":
            return

        if not self.specialist.services.filter(pk=self.service_id).exists():
            raise ValidationError({
                "service": "Этот специалист не оказывает выбранную услугу."
            })

        today = timezone.localdate()
        current_time = timezone.localtime().replace(tzinfo=None).time()

        if self.date < today:
            raise ValidationError({
                "date": "Нельзя создать запись на прошедшую дату."
            })

        if self.date == today and self.time <= current_time:
            raise ValidationError({
                "time": "Нельзя создать запись на прошедшее время."
            })

        booking_start = datetime.combine(self.date, self.time)
        current_duration = (
            self.service_duration
            if self.service_duration is not None
            else self.service.duration
        )
        booking_end = booking_start + timedelta(minutes=current_duration)

        schedule_exception = ScheduleException.objects.filter(
            specialist=self.specialist,
            date=self.date,
        ).first()

        if schedule_exception and schedule_exception.is_day_off:
            raise ValidationError({
                "date": "В этот день специалист не работает."
            })

        if schedule_exception:
            intervals = list(
                schedule_exception.intervals.values_list(
                    "start_time", "end_time"
                )
            )
        else:
            weekday = self.date.weekday()
            intervals = list(
                WorkingHour.objects.filter(
                    specialist=self.specialist,
                    is_active=True,
                    start_weekday__lte=weekday,
                    end_weekday__gte=weekday,
                ).values_list("start_time", "end_time")
            )

        fits_schedule = any(
            booking_start >= datetime.combine(self.date, start_time)
            and booking_end <= datetime.combine(self.date, end_time)
            for start_time, end_time in intervals
        )

        if not fits_schedule:
            raise ValidationError({
                "time": (
                    "Запись должна полностью помещаться "
                    "в рабочее время специалиста."
                )
            })

        existing_bookings = Booking.objects.filter(
            specialist=self.specialist,
            date=self.date,
            status="scheduled",
        ).exclude(pk=self.pk).select_related("service")

        for booking in existing_bookings:
            existing_start = datetime.combine(booking.date, booking.time)
            existing_duration = (
                booking.service_duration
                if booking.service_duration is not None
                else booking.service.duration
            )
            existing_end = existing_start + timedelta(
                minutes=existing_duration
            )

            if booking_start < existing_end and booking_end > existing_start:
                raise ValidationError({
                    "time": (
                        "Выбранное время пересекается "
                        "с другой записью этого специалиста."
                    )
                })

    def save(self, *args, **kwargs):
        if self.service_price is None:
            self.service_price = self.service.price

        if self.service_duration is None:
            self.service_duration = self.service.duration

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.customer_name} — {self.service.name} — "
            f"{self.date} {self.time}"
        )


class ScheduleException(models.Model):
    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE,
        related_name="schedule_exceptions",
        verbose_name="Специалист",
    )
    date = models.DateField(verbose_name="Дата")
    is_day_off = models.BooleanField(
        default=False,
        verbose_name="Выходной",
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Комментарий",
    )

    class Meta:
        verbose_name = "Исключение расписания"
        verbose_name_plural = "Исключения расписания"
        constraints = [
            models.UniqueConstraint(
                fields=["specialist", "date"],
                name="unique_specialist_schedule_exception",
            ),
        ]
        ordering = ["date", "specialist"]

    def __str__(self):
        return f"{self.specialist.name} — {self.date}"


class ScheduleExceptionInterval(models.Model):
    exception = models.ForeignKey(
        ScheduleException,
        on_delete=models.CASCADE,
        related_name="intervals",
        verbose_name="Исключение",
    )
    start_time = models.TimeField(verbose_name="Начало работы")
    end_time = models.TimeField(verbose_name="Конец работы")

    class Meta:
        verbose_name = "Специальный рабочий интервал"
        verbose_name_plural = "Специальные рабочие интервалы"
        ordering = ["start_time"]

    def clean(self):
        super().clean()
        if (
            self.start_time
            and self.end_time
            and self.start_time >= self.end_time
        ):
            raise ValidationError({
                "end_time": "Время окончания должно быть позже начала."
            })

    def __str__(self):
        return (
            f"{self.exception} — "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )
