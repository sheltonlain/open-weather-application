"""Tests for the OpenWeather client in weather/services.py."""

import pytest
import requests
from responses import matchers

from tests.openweather import GEO_DIRECT_URL, load_fixture
from weather.services import Place, WeatherServiceError, search_cities


def test_search_cities_calls_direct_geocoding_and_returns_places(mocked_responses):
    mocked_responses.get(
        GEO_DIRECT_URL,
        json=load_fixture("geo_direct_london.json"),
        match=[
            matchers.query_param_matcher(
                {"q": "London", "limit": "5", "appid": "test-openweather-key"}
            )
        ],
    )

    places = search_cities("London")

    assert places == [
        Place("London", "England", "GB", 51.5073219, -0.1276474),
        Place("London", "Ontario", "CA", 42.9832406, -81.243372),
        Place("London", "Ohio", "US", 39.8864493, -83.4482508),
    ]


@pytest.mark.parametrize(
    "mock_kwargs",
    [
        pytest.param({"body": requests.exceptions.Timeout()}, id="timeout"),
        pytest.param(
            {"status": 401, "json": {"cod": 401, "message": "Invalid API key"}},
            id="non-200",
        ),
        pytest.param(
            {"body": "<html>not json</html>", "content_type": "text/html"},
            id="malformed-json",
        ),
    ],
)
def test_search_cities_failure_raises_weather_service_error(
    mocked_responses, mock_kwargs
):
    mocked_responses.get(GEO_DIRECT_URL, **mock_kwargs)

    with pytest.raises(WeatherServiceError):
        search_cities("London")


def test_search_cities_handles_place_without_state(mocked_responses):
    mocked_responses.get(
        GEO_DIRECT_URL,
        json=[{"name": "Paris", "lat": 48.8588897, "lon": 2.3200410, "country": "FR"}],
    )

    assert search_cities("Paris") == [Place("Paris", "", "FR", 48.8588897, 2.320041)]


def test_search_cities_with_no_matches_returns_empty_list(mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=[])

    assert search_cities("Nowhereville") == []


def test_search_cities_drops_duplicate_places_keeping_first(mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=load_fixture("geo_direct_paris.json"))

    places = search_cities("Paris")

    assert places == [
        Place("Paris", "Ile-de-France", "FR", 48.8588897, 2.320041),
        Place("Paris", "Texas", "US", 33.6617962, -95.555513),
    ]
