"""Finish a Save that was clicked before the user logged in."""

from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from favorites.services import (
    DUPLICATE_FAVORITE_MESSAGE,
    PENDING_FAVORITE_SESSION_KEY,
    save_favorite,
    saved_message,
)


@receiver(user_logged_in)
def save_pending_favorite(sender, request, user, **kwargs) -> None:
    """Save the place an anonymous visitor tried to save, now that they're in."""
    if request is None:
        return
    place = request.session.pop(PENDING_FAVORITE_SESSION_KEY, None)
    if not place:
        return
    favorite, created = save_favorite(user, place)
    text = saved_message(favorite) if created else DUPLICATE_FAVORITE_MESSAGE
    messages.success(request, text, fail_silently=True)
