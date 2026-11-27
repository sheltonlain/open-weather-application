from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from weather.queries import parse_query
from weather.services import (
    DailyForecast,
    Place,
    WeatherServiceError,
    get_current_weather,
    get_daily_forecast,
    search_cities,
    search_zip,
)
from weather.units import METRIC, SPEED_LABELS, TEMP_LABELS, UNITS_SESSION_KEY

SEARCH_ERROR_MESSAGE = "Search is unavailable right now. Please try again."
WEATHER_ERROR_MESSAGE = "Weather is unavailable right now. Please try again."
FORECAST_ERROR_MESSAGE = "Forecast is unavailable right now. Please try again."
INVALID_LOCATION_MESSAGE = "That location is not valid. Please pick a place again."


def active_units(request: HttpRequest) -> str:
    """Return the unit system for this request: user setting, session, or metric."""
    if request.user.is_authenticated:
        return request.user.units
    return request.session.get(UNITS_SESSION_KEY, METRIC)


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


def _forecast_chart_data(forecast: list[DailyForecast], temp_unit: str) -> dict:
    """Return the data the forecast chart needs, already in display units."""
    return {
        "labels": [f"{d.date:%a} {d.date.day} {d.date:%b}" for d in forecast],
        "highs": [round(day.high, 1) for day in forecast],
        "lows": [round(day.low, 1) for day in forecast],
        "conditions": [day.description for day in forecast],
        "unit": temp_unit,
    }


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

    # The forecast fails on its own: current conditions still show without it.
    forecast = []
    forecast_error = None
    if weather:
        try:
            forecast = get_daily_forecast(*coordinates)
        except WeatherServiceError:
            forecast_error = FORECAST_ERROR_MESSAGE

    # Prefer the name the user picked: OpenWeather names its nearest station.
    name = request.GET.get("name", "").strip()
    if name:
        state = request.GET.get("state", "").strip()
        country = request.GET.get("country", "").strip()
        place = Place(name, state, country, *coordinates)
    elif weather:
        place = Place(weather.name, "", weather.country, *coordinates)
    else:
        place = None

    units = active_units(request)
    forecast = [day.in_units(units) for day in forecast]
    context = {
        "weather": weather.in_units(units) if weather else None,
        "error": error,
        "forecast": forecast,
        "forecast_chart": _forecast_chart_data(forecast, TEMP_LABELS[units]),
        "forecast_error": forecast_error,
        "place": place,
        "temp_unit": TEMP_LABELS[units],
        "speed_unit": SPEED_LABELS[units],
    }
    return render(request, template, context)
