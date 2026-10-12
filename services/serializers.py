
from rest_framework import serializers

from .models import Service, Specialist


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "price",
            "duration",
        ]


class SpecialistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialist
        fields = [
            "id",
            "name",
            "description",
            "photo",
            "experience",
        ]
