"""Shared helpers for mocking OpenWeather in tests."""

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
GEO_DIRECT_URL = "https://api.openweathermap.org/geo/1.0/direct"
GEO_ZIP_URL = "https://api.openweathermap.org/geo/1.0/zip"


def load_fixture(name: str):
    """Load a saved OpenWeather JSON response from tests/fixtures/."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))
