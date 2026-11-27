"""Template context shared by every page."""

from django.http import HttpRequest

from weather.views import active_units


def units(request: HttpRequest) -> dict:
    """Expose the active unit system so the header toggle can highlight it."""
    return {"active_units": active_units(request)}
