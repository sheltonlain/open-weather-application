from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the single-page weather dashboard."""
    return render(request, "weather/dashboard.html")
