from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from weather.queries import parse_query
from weather.services import (
    Place,
    WeatherServiceError,
    get_current_weather,
    search_cities,
    search_zip,
)

SEARCH_ERROR_MESSAGE = "Search is unavailable right now. Please try again."
WEATHER_ERROR_MESSAGE = "Weather is unavailable right now. Please try again."
INVALID_LOCATION_MESSAGE = "That location is not valid. Please pick a place again."


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


def _parse_coordinates(params) -> tuple[float, float] | None:
    """Return (lat, lon) from query parameters, or None if they are invalid."""
    try:
        lat, lon = float(params["lat"]), float(params["lon"])
    except (KeyError, ValueError):
        return None
    # NaN fails every comparison, so it is rejected here too.
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


def weather_panel(request: HttpRequest) -> HttpResponse:
    """Show current weather for the lat/lon given in the query string."""
    template = "weather/partials/weather_panel.html"
    if not request.htmx:
        template = "weather/weather.html"

    coordinates = _parse_coordinates(request.GET)
    if coordinates is None:
        context = {"error": INVALID_LOCATION_MESSAGE}
        return render(request, template, context, status=400)

    weather = None
    error = None
    try:
        weather = get_current_weather(*coordinates)
    except WeatherServiceError:
        error = WEATHER_ERROR_MESSAGE

    # Prefer the name the user picked: OpenWeather names its nearest station.
    name = request.GET.get("name", "").strip()
    if name:
        state = request.GET.get("state", "").strip()
        country = request.GET.get("country", "").strip()
        place_label = Place(name, state, country, *coordinates).label
    elif weather:
        place_label = Place(weather.name, "", weather.country, *coordinates).label
    else:
        place_label = ""

    context = {"weather": weather, "error": error, "place_label": place_label}
    return render(request, template, context)
