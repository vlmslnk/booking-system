
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from services.models import Service, Specialist

from .forms import BookingForm
from .models import Booking


def get_available_slots(service, specialist, selected_date):
    """Возвращает доступные слоты с учётом расписания и исключений."""
    exception = specialist.schedule_exceptions.filter(
        date=selected_date,
    ).prefetch_related("intervals").first()

    if exception:
        if exception.is_day_off:
            return []

        working_intervals = [
            (interval.start_time, interval.end_time)
            for interval in exception.intervals.all()
        ]
    else:
        weekday = selected_date.weekday()
        working_intervals = list(
            specialist.working_hours.filter(
                start_weekday__lte=weekday,
                end_weekday__gte=weekday,
                is_active=True,
            ).order_by("start_time").values_list(
                "start_time", "end_time"
            )
        )

    if not working_intervals:
        return []

    duration = timedelta(minutes=service.duration)
    bookings = list(
        Booking.objects.filter(
            specialist=specialist,
            date=selected_date,
            status="scheduled",
        ).select_related("service")
    )

    current_datetime = timezone.localtime()
    available_slots = set()

    for start_time, end_time in working_intervals:
        current_time = datetime.combine(selected_date, start_time)
        working_end = datetime.combine(selected_date, end_time)

        while current_time + duration <= working_end:
            slot_start = current_time
            slot_end = slot_start + duration

            if (
                selected_date == current_datetime.date()
                and slot_start.time() <= current_datetime.time()
            ):
                current_time += timedelta(minutes=30)
                continue

            is_available = True

            for booking in bookings:
                booking_start = datetime.combine(
                    booking.date, booking.time
                )
                booking_end = booking_start + timedelta(
                    minutes=(booking.service_duration if booking.service_duration is not None else booking.service.duration)
                )

                if slot_start < booking_end and slot_end > booking_start:
                    is_available = False
                    break

            if is_available:
                available_slots.add(current_time.strftime("%H:%M"))

            current_time += timedelta(minutes=30)

    return sorted(available_slots)


@login_required
def create_booking(request, service_id, specialist_id):
    service = get_object_or_404(
        Service,
        pk=service_id,
        is_active=True,
    )

    specialist = get_object_or_404(
        Specialist,
        pk=specialist_id,
        is_active=True,
    )

    # Проверяем, оказывает ли специалист выбранную услугу.
    if not specialist.services.filter(pk=service.pk).exists():
        return redirect("services:service_list")

    selected_date = None
    available_slots = []

    if request.method == "POST":
        form = BookingForm(request.POST)

        if form.is_valid():
            selected_date = form.cleaned_data["date"]

            available_slots = get_available_slots(
                service,
                specialist,
                selected_date,
            )

            selected_time = form.cleaned_data["time"]

            if selected_time.strftime("%H:%M") not in available_slots:
                form.add_error(
                    "time",
                    "Это время уже недоступно. Выберите другое.",
                )
            else:
                booking = form.save(commit=False)
                booking.user = request.user
                booking.service = service
                booking.specialist = specialist

                try:
                    booking.save()
                except ValidationError as error:
                    for field, errors in error.message_dict.items():
                        for message in errors:
                            form.add_error(field, message)

                    available_slots = get_available_slots(
                        service,
                        specialist,
                        selected_date,
                    )
                else:
                    return redirect(
                        "bookings:booking_success",
                        booking_id=booking.pk,
                    )
    else:
        form = BookingForm()

        date_value = request.GET.get("date")

        if date_value:
            try:
                selected_date = datetime.strptime(
                    date_value,
                    "%Y-%m-%d",
                ).date()
            except ValueError:
                selected_date = None

        if selected_date:
            available_slots = get_available_slots(
                service,
                specialist,
                selected_date,
            )

    context = {
        "form": form,
        "service": service,
        "specialist": specialist,
        "selected_date": selected_date,
        "available_slots": available_slots,
    }

    return render(
        request,
        "bookings/create_booking.html",
        context,
    )


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related(
            "service",
            "specialist",
        ),
        pk=booking_id,
        user=request.user,
    )

    return render(
        request,
        "bookings/booking_success.html",
        {"booking": booking},
    )


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        user=request.user,
    )

    if request.method == "POST":
        if booking.status == "scheduled":
            booking.status = "cancelled"
            booking.save()

        return redirect("bookings:my_bookings")

    return render(
        request,
        "bookings/cancel_booking.html",
        {"booking": booking},
    )


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(
        user=request.user,
    ).select_related(
        "service",
        "specialist",
    )

    return render(
        request,
        "bookings/my_bookings.html",
        {"bookings": bookings},
    )
