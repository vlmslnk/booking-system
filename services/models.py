from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(
        help_text="Duration in minutes"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Specialist(models.Model):
    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    photo = models.ImageField(
        upload_to="specialists/",
        blank=True,
        null=True
    )

    experience = models.PositiveIntegerField(
        default=0,
        help_text="Опыт работы в годах"
    )

    is_active = models.BooleanField(
        default=True
    )

    services = models.ManyToManyField(
        Service,
        related_name="specialists",
        blank=True
    )

    def __str__(self):
        return self.name

class PortfolioImage(models.Model):
    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE,
        related_name="portfolio",
    )

    image = models.ImageField(
        upload_to="portfolio/",
    )

    title = models.CharField(
        max_length=200,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.specialist.name} — {self.title}"