from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from bookings.models import Booking

from .forms import RegistrationForm


def register(request):

    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.set_password(
                form.cleaned_data["password"]
            )

            user.save()

            login(request, user)

            return redirect("profile")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            login(request, user)

            return redirect("profile")

        error = "Неверное имя пользователя или пароль."

    else:
        error = None

    return render(
        request,
        "accounts/login.html",
        {
            "error": error,
        },
    )


@login_required
def profile(request):

    bookings = Booking.objects.filter(
        user=request.user
    ).select_related(
        "service",
        "specialist",
    )

    upcoming_bookings = bookings.filter(
        status="scheduled"
    )

    completed_bookings = bookings.filter(
        status="completed"
    )

    cancelled_bookings = bookings.filter(
        status="cancelled"
    )

    context = {
        "bookings": bookings,
        "upcoming_bookings": upcoming_bookings,
        "completed_bookings": completed_bookings,
        "cancelled_bookings": cancelled_bookings,

        "total_count": bookings.count(),
        "upcoming_count": upcoming_bookings.count(),
        "completed_count": completed_bookings.count(),
        "cancelled_count": cancelled_bookings.count(),
    }

    return render(
        request,
        "accounts/profile.html",
        context,
    )


def logout_view(request):

    logout(request)

    return redirect("service_list")