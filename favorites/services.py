"""Saving favorites, shared by the add view and the after-login hook."""

from favorites.models import COORDINATE_DECIMALS, Favorite

PENDING_FAVORITE_SESSION_KEY = "pending_favorite"
DUPLICATE_FAVORITE_MESSAGE = "That place is already in your favorites."


def save_favorite(user, place: dict) -> tuple[Favorite, bool]:
    """Save a place for the user, rounding lat/lon; return (favorite, created)."""
    details = dict(place)
    lat = round(details.pop("lat"), COORDINATE_DECIMALS)
    lon = round(details.pop("lon"), COORDINATE_DECIMALS)
    return Favorite.objects.get_or_create(user=user, lat=lat, lon=lon, defaults=details)


def saved_message(favorite: Favorite) -> str:
    """Return the confirmation shown after a favorite is saved."""
    return f"Saved {favorite.place.label} to your favorites."
