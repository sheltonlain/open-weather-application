from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Site user with a preferred unit system for weather data."""

    class Units(models.TextChoices):
        METRIC = "metric", "Metric (°C, m/s)"
        IMPERIAL = "imperial", "Imperial (°F, mph)"

    units = models.CharField(max_length=10, choices=Units.choices, default=Units.METRIC)
