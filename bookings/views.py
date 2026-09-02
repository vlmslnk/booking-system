from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from services.models import Service, Specialist

from .forms import BookingForm
from .models import Booking


def get_available_slots(service, specialist, selected_date):
    """
    Возвращает список свободных временных слотов
    для выбранной услуги, специалиста и даты.
    """

    weekday = selected_date.weekday()

    working_hour = specialist.working_hours.filter(
        start_weekday__lte=weekday,
        end_weekday__gte=weekday,
        is_active=True,
    ).first()

    if not working_hour:
        return []

    current_time = datetime.combine(
        selected_date,
        working_hour.start_time,
    )

    working_end = datetime.combine(
        selected_date,
        working_hour.end_time,
    )

    duration = timedelta(
        minutes=service.duration
    )

    bookings = Booking.objects.filter(
        specialist=specialist,
        date=selected_date,
    ).select_related("service")

    available_slots = []

    # Текущее время для сегодняшнего дня
    current_datetime = timezone.localtime()

    while current_time + duration <= working_end:

        slot_start = current_time
        slot_end = current_time + duration

        # Не показываем уже прошедшее время сегодня
        if selected_date == current_datetime.date():
            if slot_start.time() <= current_datetime.time():
                current_time += timedelta(minutes=30)
                continue

        is_available = True

        for booking in bookings:

            booking_start = datetime.combine(
                selected_date,
                booking.time,
            )

            booking_end = booking_start + timedelta(
                minutes=booking.service.duration
            )

            # Проверяем пересечение времени
            if (
                slot_start < booking_end
                and slot_end > booking_start
            ):
                is_available = False
                break

        if is_available:
            available_slots.append(
                current_time.strftime("%H:%M")
            )

        current_time += timedelta(minutes=30)

    return available_slots


@login_required
def create_booking(request, service_id, specialist_id):

    service = get_object_or_404(
        Service,
        id=service_id,
        is_active=True,
    )

    specialist = get_object_or_404(
        Specialist,
        id=specialist_id,
        is_active=True,
    )

    # Проверяем, оказывает ли специалист эту услугу
    if not specialist.services.filter(
        id=service.id
    ).exists():
        return redirect("service_list")

    today = timezone.localdate()

    selected_date = request.GET.get("date")

    available_slots = []

    # Если дата выбрана через GET
    if selected_date:

        try:
            selected_date = datetime.strptime(
                selected_date,
                "%Y-%m-%d",
            ).date()

            if selected_date < today:
                selected_date = None
            else:
                available_slots = get_available_slots(
                    service,
                    specialist,
                    selected_date,
                )

        except ValueError:
            selected_date = None

    # Обработка бронирования
    if request.method == "POST":

        form = BookingForm(request.POST)

        date_value = request.POST.get("date")

        if date_value:

            try:
                form_date = datetime.strptime(
                    date_value,
                    "%Y-%m-%d",
                ).date()

                # Не позволяем отправить прошедшую дату
                if form_date < today:
                    form.add_error(
                        "date",
                        "Нельзя выбрать прошедшую дату.",
                    )
                else:
                    available_slots = get_available_slots(
                        service,
                        specialist,
                        form_date,
                    )

                    form.fields["time"].choices = [
                        (slot, slot)
                        for slot in available_slots
                    ]

            except ValueError:
                pass

        if form.is_valid():

            booking = form.save(commit=False)

            booking.user = request.user
            booking.service = service
            booking.specialist = specialist

            # Повторно проверяем доступность времени
            selected_slots = get_available_slots(
                service,
                specialist,
                booking.date,
            )

            selected_time = booking.time.strftime(
                "%H:%M"
            )

            if selected_time not in selected_slots:

                form.add_error(
                    "time",
                    "Это время уже занято или недоступно.",
                )

            else:

                booking.save()

                return redirect(
                    "booking_success",
                    booking_id=booking.id,
                )

    else:

        form = BookingForm()

        if available_slots:

            form.fields["time"].choices = [
                (slot, slot)
                for slot in available_slots
            ]

        else:

            form.fields["time"].choices = [
                ("", "Сначала выберите дату")
            ]

        selected_time = request.GET.get("time")

        if selected_time:
            form.fields["time"].initial = selected_time

    return render(
        request,
        "bookings/create_booking.html",
        {
            "form": form,
            "service": service,
            "specialist": specialist,
            "available_slots": available_slots,
            "selected_date": selected_date,
            "today": today,
        },
    )


def booking_success(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
    )

    return render(
        request,
        "bookings/booking_success.html",
        {
            "booking": booking,
        },
    )

@login_required
def cancel_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user,
    )

    if request.method == "POST":

        booking.status = "cancelled"
        booking.save(update_fields=["status"])

        return redirect("profile")

    return redirect("profile")