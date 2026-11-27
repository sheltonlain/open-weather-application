from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.forms import RegisterForm
from accounts.models import User
from weather.units import UNITS_SESSION_KEY


def register(request: HttpRequest) -> HttpResponse:
    """Show the registration form; on valid POST create the user and log in."""
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("dashboard")
    return render(request, "accounts/register.html", {"form": form})


@require_POST
def set_units(request: HttpRequest) -> HttpResponse:
    """Save the chosen unit system on the user, or in the session if anonymous."""
    units = request.POST.get("units", "")
    if units not in User.Units.values:
        return HttpResponseBadRequest("Unknown unit system.")

    if request.user.is_authenticated:
        request.user.units = units
        request.user.save(update_fields=["units"])
    else:
        request.session[UNITS_SESSION_KEY] = units

    next_url = request.POST.get("next", "")
    if request.htmx:
        # Re-render the toggle; the weather panel hears the event and reloads.
        response = render(
            request,
            "accounts/partials/units_toggle.html",
            {"active_units": units, "units_next": next_url},
        )
        response["HX-Trigger"] = "unitsChanged"
        return response

    messages.success(request, "Units saved.")
    if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
        next_url = reverse("dashboard")
    return redirect(next_url)


@login_required
def settings(request: HttpRequest) -> HttpResponse:
    """Show the unit preference form; it posts to set_units."""
    return render(
        request, "accounts/settings.html", {"unit_choices": User.Units.choices}
    )
