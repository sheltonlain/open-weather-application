"""OpenWeather client: the only module that talks to the OpenWeather API."""

from collections import Counter
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.cache import cache

from weather.units import IMPERIAL, celsius_to_fahrenheit, ms_to_mph

BASE_URL = "https://api.openweathermap.org"
TIMEOUT_SECONDS = 5
SEARCH_LIMIT = 5
FORECAST_DAYS = 5
CACHE_SECONDS = 10 * 60  # OpenWeather updates its data about every 10 minutes.

# Emoji per OpenWeather icon group, so the browser never loads OpenWeather URLs.
ICON_EMOJI = {
    "01": "☀️",
    "02": "⛅",
    "03": "☁️",
    "04": "☁️",
    "09": "🌧️",
    "10": "🌦️",
    "11": "⛈️",
    "13": "❄️",
    "50": "🌫️",
}


def icon_emoji(icon: str) -> str:
    """Return an emoji for an OpenWeather icon code (e.g. "04d")."""
    if icon == "01n":
        return "🌙"
    return ICON_EMOJI.get(icon[:2], "🌡️")


class WeatherServiceError(Exception):
    """OpenWeather could not be reached or returned an unusable response."""


class NotFoundError(WeatherServiceError):
    """OpenWeather answered 404: the requested place does not exist."""


@dataclass(frozen=True)
class Place:
    """A geocoded location."""

    name: str
    state: str
    country: str
    lat: float
    lon: float

    @property
    def label(self) -> str:
        """Return "name, state, country", skipping any empty part."""
        return ", ".join(part for part in (self.name, self.state, self.country) if part)

    @property
    def query_string(self) -> str:
        """Return the query string that loads this place's weather panel."""
        return urlencode(
            {
                "lat": self.lat,
                "lon": self.lon,
                "name": self.name,
                "state": self.state,
                "country": self.country,
            }
        )


@dataclass(frozen=True)
class CurrentWeather:
    """Current conditions for one place, in metric units."""

    name: str
    country: str
    description: str
    icon: str
    temp: float
    feels_like: float
    humidity: int
    wind_speed: float
    clouds: int
    pressure: int
    sunrise: time
    sunset: time

    @property
    def emoji(self) -> str:
        """Return an emoji for this weather's icon."""
        return icon_emoji(self.icon)

    def in_units(self, units: str) -> "CurrentWeather":
        """Return a copy with temperatures and wind in the given unit system."""
        if units != IMPERIAL:
            return self
        return replace(
            self,
            temp=celsius_to_fahrenheit(self.temp),
            feels_like=celsius_to_fahrenheit(self.feels_like),
            wind_speed=ms_to_mph(self.wind_speed),
        )


@dataclass(frozen=True)
class DailyForecast:
    """One forecast day's high, low and main condition, in metric units."""

    date: date
    high: float
    low: float
    description: str
    icon: str

    @property
    def emoji(self) -> str:
        """Return an emoji for this day's icon."""
        return icon_emoji(self.icon)

    def in_units(self, units: str) -> "DailyForecast":
        """Return a copy with the high and low in the given unit system."""
        if units != IMPERIAL:
            return self
        return replace(
            self,
            high=celsius_to_fahrenheit(self.high),
            low=celsius_to_fahrenheit(self.low),
        )


def _get_json(path: str, params: dict) -> list | dict:
    """GET an OpenWeather endpoint with the API key and return its JSON body."""
    try:
        response = requests.get(
            BASE_URL + path,
            params={**params, "appid": settings.OPENWEATHER_API_KEY},
            timeout=TIMEOUT_SECONDS,
        )
        if response.status_code == 404:
            raise NotFoundError(f"OpenWeather found nothing at {path}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        # "from None" drops the original error, whose message contains the full
        # URL including the API key, so the key never ends up in logs.
        raise WeatherServiceError(f"OpenWeather request to {path} failed") from None


def _get_cached_json(path: str, lat: float, lon: float) -> dict:
    """GET a lat/lon endpoint in metric units, cached by endpoint and position."""
    lat, lon = round(lat, 4), round(lon, 4)
    key = f"openweather:{path}:{lat:.4f}:{lon:.4f}"
    data = cache.get(key)
    if data is None:
        data = _get_json(path, {"lat": lat, "lon": lon, "units": "metric"})
        cache.set(key, data, CACHE_SECONDS)
    return data


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


def search_zip(zip_query: str) -> list[Place]:
    """Return the place for a "<code>,<country>" ZIP query, or an empty list."""
    try:
        item = _get_json("/geo/1.0/zip", {"zip": zip_query})
    except NotFoundError:
        return []
    return [
        Place(
            name=item["name"],
            state="",
            country=item["country"],
            lat=item["lat"],
            lon=item["lon"],
        )
    ]


def _local_time(timestamp: int, utc_offset_seconds: int) -> time:
    """Return the wall-clock time at a place for a UTC Unix timestamp."""
    place_tz = timezone(timedelta(seconds=utc_offset_seconds))
    return datetime.fromtimestamp(timestamp, place_tz).time()


def get_current_weather(lat: float, lon: float) -> CurrentWeather:
    """Return current weather at the given coordinates (metric units)."""
    data = _get_cached_json("/data/2.5/weather", lat, lon)
    try:
        condition = data["weather"][0]
        offset = data["timezone"]
        return CurrentWeather(
            name=data["name"],
            country=data["sys"].get("country", ""),
            description=condition["description"],
            icon=condition["icon"],
            temp=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            humidity=data["main"]["humidity"],
            wind_speed=data["wind"]["speed"],
            clouds=data["clouds"]["all"],
            pressure=data["main"]["pressure"],
            sunrise=_local_time(data["sys"]["sunrise"], offset),
            sunset=_local_time(data["sys"]["sunset"], offset),
        )
    except (KeyError, IndexError, TypeError):
        raise WeatherServiceError("OpenWeather sent unexpected weather data") from None


def get_daily_forecast(lat: float, lon: float) -> list[DailyForecast]:
    """Return up to 5 days of forecast highs, lows and conditions (metric)."""
    data = _get_cached_json("/data/2.5/forecast", lat, lon)
    try:
        place_tz = timezone(timedelta(seconds=data["city"]["timezone"]))
        steps_by_day: dict[date, list[dict]] = {}
        for step in data["list"]:
            day = datetime.fromtimestamp(step["dt"], place_tz).date()
            steps_by_day.setdefault(day, []).append(step)
        return [
            _summarize_day(day, steps)
            for day, steps in list(steps_by_day.items())[:FORECAST_DAYS]
        ]
    except (KeyError, IndexError, TypeError):
        raise WeatherServiceError("OpenWeather sent unexpected forecast data") from None


def _summarize_day(day: date, steps: list[dict]) -> DailyForecast:
    """Combine one day's 3-hour steps into its high, low and main condition."""
    temps = [step["main"]["temp"] for step in steps]
    conditions = [step["weather"][0] for step in steps]
    # The most frequent description wins; ties go to the earliest one.
    description = Counter(c["description"] for c in conditions).most_common(1)[0][0]
    icon = next(c["icon"] for c in conditions if c["description"] == description)
    return DailyForecast(
        date=day,
        high=max(temps),
        low=min(temps),
        description=description,
        icon=icon[:2] + "d",  # a day summary always uses the daytime icon
    )
