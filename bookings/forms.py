from datetime import date, datetime

from django import forms

from .models import Booking


class BookingForm(forms.ModelForm):

    class Meta:
        model = Booking

        fields = [
            "customer_name",
            "customer_phone",
            "date",
            "time",
        ]

        widgets = {
            "customer_name": forms.TextInput(
                attrs={
                    "placeholder": "Ваше имя",
                }
            ),

            "customer_phone": forms.TextInput(
                attrs={
                    "placeholder": "Ваш телефон",
                }
            ),

            "date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "time": forms.Select(
                attrs={
                    "id": "id_time",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        selected_date = cleaned_data.get("date")
        selected_time = cleaned_data.get("time")

        # -----------------------------
        # Проверка даты
        # -----------------------------

        if selected_date:

            if selected_date < date.today():

                self.add_error(
                    "date",
                    "Нельзя выбрать прошедшую дату.",
                )

        # -----------------------------
        # Проверка времени
        # -----------------------------

        if selected_date and selected_time:

            if isinstance(selected_time, str):

                try:
                    selected_time = datetime.strptime(
                        selected_time,
                        "%H:%M",
                    ).time()

                except ValueError:

                    self.add_error(
                        "time",
                        "Выберите корректное время.",
                    )

                    return cleaned_data

            # Если выбрано сегодня
            if selected_date == date.today():

                current_time = datetime.now().time()

                if selected_time <= current_time:

                    self.add_error(
                        "time",
                        "Это время уже прошло.",
                    )

        return cleaned_data