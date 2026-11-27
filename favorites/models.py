from django.conf import settings
from django.db import models

from weather.services import Place

COORDINATE_DECIMALS = 4


class FavoriteQuerySet(models.QuerySet):
    """Favorites queries, also usable as ``user.favorites.<method>``."""

    def default(self) -> "Favorite | None":
        """Return the default favorite, or None if there is none."""
        return self.filter(is_default=True).first()

    def default_first(self) -> "models.QuerySet[Favorite]":
        """Return the favorites with the default one first, then oldest first."""
        return self.order_by("-is_default", "created_at", "id")


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
    # The place the dashboard opens on; at most one per user.
    is_default = models.BooleanField(default=False)

    objects = FavoriteQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "lat", "lon"], name="unique_favorite_per_user"
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="one_default_favorite_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.user})"

    @property
    def place(self) -> Place:
        """Return this favorite as a Place, ready for labels and weather links."""
        return Place(
            self.name, self.state, self.country, float(self.lat), float(self.lon)
        )
