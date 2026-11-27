from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRedirect

from favorites.forms import FavoriteForm
from favorites.models import COORDINATE_DECIMALS, Favorite

INVALID_FAVORITE_MESSAGE = "That place could not be saved. Please try again."
DUPLICATE_FAVORITE_MESSAGE = "That place is already in your favorites."


def login_required_htmx(view):
    """Like login_required, but HTMX requests get a full-page redirect to login.

    A plain 302 would make HTMX swap the login page into the sidebar, so
    anonymous HTMX requests get HX-Redirect back to login, with ``next`` set to
    the page the user was on.
    """

    @wraps(view)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.htmx and not request.user.is_authenticated:
            next_url = request.htmx.current_url_abs_path or reverse("dashboard")
            login_url = redirect_to_login(next_url).url
            return HttpResponseClientRedirect(login_url)
        return login_required(view)(request, *args, **kwargs)

    return wrapper


def _render_list(
    request: HttpRequest, message: str = "", status: int = 200
) -> HttpResponse:
    """Render the user's favorites: the sidebar partial, or a full page."""
    template = "favorites/partials/favorites_list.html"
    if not request.htmx:
        template = "favorites/favorites.html"
    context = {"favorites": request.user.favorites.all(), "message": message}
    return render(request, template, context, status=status)


@login_required_htmx
@require_http_methods(["GET", "POST"])
def favorites(request: HttpRequest) -> HttpResponse:
    """List the user's favorites (GET) or save a new one (POST)."""
    if request.method == "GET":
        return _render_list(request)

    form = FavoriteForm(request.POST)
    if not form.is_valid():
        return _render_list(request, INVALID_FAVORITE_MESSAGE, status=400)

    place = form.cleaned_data
    lat = round(place.pop("lat"), COORDINATE_DECIMALS)
    lon = round(place.pop("lon"), COORDINATE_DECIMALS)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user, lat=lat, lon=lon, defaults=place
    )
    if not created:
        return _render_list(request, DUPLICATE_FAVORITE_MESSAGE)

    saved_message = f"Saved {favorite.place.label} to your favorites."
    if not request.htmx:
        messages.success(request, saved_message)
        return redirect("dashboard")
    return _render_list(request, saved_message, status=201)


@login_required_htmx
@require_http_methods(["DELETE"])
def remove_favorite(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete one of the user's favorites; anyone else's is a 404."""
    favorite = get_object_or_404(Favorite, pk=pk, user=request.user)
    favorite.delete()
    return _render_list(request)
