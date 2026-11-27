from django.conf import settings
from django.db import models

from weather.services import Place

COORDINATE_DECIMALS = 4


class Favorite(models.Model):
    """A place a user saved, stored as a snapshot of the geocoded result."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    name = models.CharField(max_length=200)
    state = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=2, blank=True)
    lat = models.DecimalField(max_digits=7, decimal_places=COORDINATE_DECIMALS)
    lon = models.DecimalField(max_digits=8, decimal_places=COORDINATE_DECIMALS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "lat", "lon"], name="unique_favorite_per_user"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.user})"

    @property
    def place(self) -> Place:
        """Return this favorite as a Place, ready for labels and weather links."""
        return Place(
            self.name, self.state, self.country, float(self.lat), float(self.lon)
        )
