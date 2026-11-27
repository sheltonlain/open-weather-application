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
from favorites.models import Favorite
from favorites.services import (
    DUPLICATE_FAVORITE_MESSAGE,
    PENDING_FAVORITE_SESSION_KEY,
    save_favorite,
    saved_message,
)

INVALID_FAVORITE_MESSAGE = "That place could not be saved. Please try again."


def login_required_htmx(view):
    """Like login_required, but HTMX requests get a full-page redirect to login.

    A plain 302 would make HTMX swap the login page into the sidebar, so
    anonymous HTMX requests get HX-Redirect back to login, with ``next`` set to
    the page the user was on. An anonymous Save (a valid POST) is kept in the
    session, and the user_logged_in hook saves it once they log in.
    """

    @wraps(view)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.method == "POST" and not request.user.is_authenticated:
            form = FavoriteForm(request.POST)
            if form.is_valid():
                request.session[PENDING_FAVORITE_SESSION_KEY] = form.cleaned_data
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

    favorite, created = save_favorite(request.user, form.cleaned_data)
    if not created:
        return _render_list(request, DUPLICATE_FAVORITE_MESSAGE)

    message = saved_message(favorite)
    if not request.htmx:
        messages.success(request, message)
        return redirect("dashboard")
    return _render_list(request, message, status=201)


@login_required_htmx
@require_http_methods(["DELETE"])
def remove_favorite(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete one of the user's favorites; anyone else's is a 404."""
    favorite = get_object_or_404(Favorite, pk=pk, user=request.user)
    favorite.delete()
    return _render_list(request)
