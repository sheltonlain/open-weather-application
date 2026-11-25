from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from weather.queries import parse_query
from weather.services import WeatherServiceError, search_cities, search_zip

SEARCH_ERROR_MESSAGE = "Search is unavailable right now. Please try again."


def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the single-page weather dashboard."""
    return render(request, "weather/dashboard.html")


def search(request: HttpRequest) -> HttpResponse:
    """Search for places by city name or ZIP/postal code."""
    query = request.GET.get("q", "").strip()
    places = []
    error = None
    if query:
        parsed = parse_query(query)
        lookup = search_zip if parsed.kind == "zip" else search_cities
        try:
            places = lookup(parsed.value)
        except WeatherServiceError:
            error = SEARCH_ERROR_MESSAGE

    context = {"query": query, "places": places, "error": error}
    template = "weather/partials/search_results.html"
    if not request.htmx:
        template = "weather/search.html"
    return render(request, template, context)
