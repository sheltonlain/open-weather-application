"""Pure helpers that convert OpenWeather's metric values to imperial units."""

METRES_PER_MILE = 1609.344
SECONDS_PER_HOUR = 3600


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from degrees Celsius to degrees Fahrenheit."""
    return celsius * 9 / 5 + 32


def ms_to_mph(ms: float) -> float:
    """Convert a speed from metres per second to miles per hour."""
    return ms * SECONDS_PER_HOUR / METRES_PER_MILE


METRIC = "metric"
IMPERIAL = "imperial"
TEMP_LABELS = {METRIC: "°C", IMPERIAL: "°F"}
SPEED_LABELS = {METRIC: "m/s", IMPERIAL: "mph"}
UNITS_SESSION_KEY = "units"  # where an anonymous visitor's choice is stored
