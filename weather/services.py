"""OpenWeather client: the only module that talks to the OpenWeather API."""

from dataclasses import dataclass

import requests
from django.conf import settings

BASE_URL = "https://api.openweathermap.org"
TIMEOUT_SECONDS = 5
SEARCH_LIMIT = 5


class WeatherServiceError(Exception):
    """OpenWeather could not be reached or returned an unusable response."""


@dataclass(frozen=True)
class Place:
    """A geocoded location."""

    name: str
    state: str
    country: str
    lat: float
    lon: float


def _get_json(path: str, params: dict) -> list | dict:
    """GET an OpenWeather endpoint with the API key and return its JSON body."""
    try:
        response = requests.get(
            BASE_URL + path,
            params={**params, "appid": settings.OPENWEATHER_API_KEY},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        # "from None" drops the original error, whose message contains the full
        # URL including the API key, so the key never ends up in logs.
        raise WeatherServiceError(f"OpenWeather request to {path} failed") from None


def search_cities(query: str) -> list[Place]:
    """Return up to 5 distinct places matching a city name."""
    data = _get_json("/geo/1.0/direct", {"q": query, "limit": SEARCH_LIMIT})
    places = []
    seen = set()
    for item in data:
        place = Place(
            name=item["name"],
            state=item.get("state", ""),
            country=item["country"],
            lat=item["lat"],
            lon=item["lon"],
        )
        # OpenWeather can list the same place twice with slightly different
        # coordinates; keep only the first (best-ranked) one.
        label = (place.name, place.state, place.country)
        if label not in seen:
            seen.add(label)
            places.append(place)
    return places
