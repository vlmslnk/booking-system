from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from services.models import Service, Specialist
from bookings.models import Booking, WorkingHour
from bookings.views import get_available_slots


class BookingScheduleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        self.service = Service.objects.create(
            name="Стрижка",
            description="Тестовая услуга",
            price=Decimal("20.00"),
            duration=60,
        )

        self.specialist = Specialist.objects.create(
            name="Тестовый специалист",
        )

        self.specialist.services.add(self.service)

        # Старый формат: специалист работает
        # с понедельника по пятницу, 09:00–12:00.
        self.working_hour = WorkingHour.objects.create(
            specialist=self.specialist,
            start_weekday=0,
            end_weekday=4,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )

        # Будущий понедельник, чтобы не зависеть
        # от текущего дня и прошедшего времени.
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7

        self.selected_date = today + timedelta(
            days=days_until_monday
        )

    def test_slots_fit_inside_working_interval(self):
        slots = get_available_slots(
            self.service,
            self.specialist,
            self.selected_date,
        )

        self.assertIn("09:00", slots)
        self.assertIn("10:00", slots)
        self.assertIn("11:00", slots)
        self.assertNotIn("11:30", slots)

    def test_overlapping_bookings_are_rejected(self):
        Booking.objects.create(
            user=self.user,
            service=self.service,
            specialist=self.specialist,
            customer_name="Первый клиент",
            customer_phone="123456789",
            date=self.selected_date,
            time=time(9, 0),
        )

        overlapping_booking = Booking(
            user=self.user,
            service=self.service,
            specialist=self.specialist,
            customer_name="Второй клиент",
            customer_phone="987654321",
            date=self.selected_date,
            time=time(9, 30),
        )

        with self.assertRaises(ValidationError):
            overlapping_booking.save()

    def test_multiple_working_intervals(self):
        WorkingHour.objects.create(
            specialist=self.specialist,
            start_weekday=0,
            end_weekday=4,
            start_time=time(13, 0),
            end_time=time(16, 0),
        )

        slots = get_available_slots(
            self.service,
            self.specialist,
            self.selected_date,
        )

        self.assertIn("09:00", slots)
        self.assertIn("13:00", slots)
        self.assertIn("15:00", slots)
        self.assertNotIn("15:30", slots)

    def test_day_off_exception_blocks_all_slots(self):
        from bookings.models import ScheduleException

        ScheduleException.objects.create(
            specialist=self.specialist,
            date=self.selected_date,
            is_day_off=True,
            note="Выходной",
        )

        slots = get_available_slots(
            self.service,
            self.specialist,
            self.selected_date,
        )

        self.assertEqual(slots, [])

    def test_special_intervals_override_weekly_schedule(self):
        from bookings.models import (
            ScheduleException,
            ScheduleExceptionInterval,
        )

        exception = ScheduleException.objects.create(
            specialist=self.specialist,
            date=self.selected_date,
            is_day_off=False,
            note="Особый график",
        )

        ScheduleExceptionInterval.objects.create(
            exception=exception,
            start_time=time(14, 0),
            end_time=time(17, 0),
        )

        slots = get_available_slots(
            self.service,
            self.specialist,
            self.selected_date,
        )

        self.assertIn("14:00", slots)
        self.assertIn("16:00", slots)
        self.assertNotIn("09:00", slots)
        self.assertNotIn("16:30", slots)

    def test_booking_keeps_original_service_price_and_duration(self):
        booking = Booking.objects.create(
            user=self.user,
            service=self.service,
            specialist=self.specialist,
            customer_name="Клиент снимка",
            customer_phone="123456789",
            date=self.selected_date,
            time=time(9, 0),
        )

        self.service.price = Decimal("35.00")
        self.service.duration = 90
        self.service.save()

        booking.refresh_from_db()

        self.assertEqual(booking.service_price, Decimal("20.00"))
        self.assertEqual(booking.service_duration, 60)


from rest_framework.test import APITestCase


class BookingAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="api_test_user",
            password="testpassword123",
        )

        self.service = Service.objects.create(
            name="API-стрижка",
            description="Услуга для API-тестов",
            price=Decimal("20.00"),
            duration=60,
        )

        self.specialist = Specialist.objects.create(
            name="API-специалист",
        )
        self.specialist.services.add(self.service)

        WorkingHour.objects.create(
            specialist=self.specialist,
            start_weekday=0,
            end_weekday=4,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )

        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7

        self.selected_date = today + timedelta(
            days=days_until_monday
        )

        self.client.force_authenticate(user=self.user)

        self.url = "/api/bookings/"

        self.payload = {
            "service": self.service.pk,
            "specialist": self.specialist.pk,
            "customer_name": "Тестовый клиент",
            "customer_phone": "123456789",
            "date": self.selected_date.isoformat(),
            "time": "09:00",
        }

    def test_create_booking_returns_201(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Booking.objects.filter(
                user=self.user,
                service=self.service,
                specialist=self.specialist,
                date=self.selected_date,
                time=time(9, 0),
            ).exists()
        )

    def test_invalid_service_returns_400(self):
        payload = self.payload.copy()
        payload["service"] = 999999

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_overlapping_booking_returns_409(self):
        Booking.objects.create(
            user=self.user,
            service=self.service,
            specialist=self.specialist,
            customer_name="Первый клиент",
            customer_phone="111111111",
            date=self.selected_date,
            time=time(9, 0),
        )

        payload = self.payload.copy()
        payload["time"] = "09:30"

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {
                "code": "slot_unavailable",
                "detail": "Это время уже занято. Выберите другой слот.",
            },
        )
