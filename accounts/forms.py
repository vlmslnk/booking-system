from django import forms
from django.contrib.auth.models import User


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Введите пароль",
            }
        ),
    )

    password_confirm = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Повторите пароль",
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
        ]

        labels = {
            "username": "Имя пользователя",
            "email": "Email",
        }

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "placeholder": "Введите имя пользователя",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Введите email",
                }
            ),
        }

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(
            username=username
        ).exists():
            raise forms.ValidationError(
                "Пользователь с таким именем уже существует."
            )

        return username

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                self.add_error(
                    "password_confirm",
                    "Пароли не совпадают.",
                )

        return cleaned_data