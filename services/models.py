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
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    services = models.ManyToManyField(
        Service,
        related_name="specialists",
        blank=True
    )

    def __str__(self):
        return self.name