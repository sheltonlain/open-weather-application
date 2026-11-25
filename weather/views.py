from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from weather.services import WeatherServiceError, search_cities

SEARCH_ERROR_MESSAGE = "Search is unavailable right now. Please try again."


def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the single-page weather dashboard."""
    return render(request, "weather/dashboard.html")


def search(request: HttpRequest) -> HttpResponse:
    """Search for places by city name."""
    query = request.GET.get("q", "").strip()
    places = []
    error = None
    if query:
        try:
            places = search_cities(query)
        except WeatherServiceError:
            error = SEARCH_ERROR_MESSAGE

    context = {"query": query, "places": places, "error": error}
    template = "weather/partials/search_results.html"
    if not request.htmx:
        template = "weather/search.html"
    return render(request, template, context)
