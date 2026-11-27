"""Tests for the weather map (marker data for the selected place and favorites)."""

import json
import re

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains
from responses import matchers

from tests.factories import FavoriteFactory, UserFactory
from tests.openweather import FORECAST_URL, WEATHER_URL, load_fixture

NEW_YORK = {"lat": "40.7484", "lon": "-73.9967", "name": "New York", "country": "US"}


def get_panel(client, params=NEW_YORK):
    """GET the weather panel partial the way HTMX does."""
    return client.get(reverse("weather"), params, headers={"HX-Request": "true"})


def map_data(response) -> dict:
    """Return the map marker data emitted by the json_script tag."""
    match = re.search(
        r'<script id="weather-map-data" type="application/json">(.*?)</script>',
        response.content.decode(),
    )
    assert match, "map data not found"
    return json.loads(match.group(1))


@pytest.mark.django_db
def test_selected_marker_uses_the_active_units(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    client.force_login(UserFactory(units="imperial"))

    selected = map_data(get_panel(client))["selected"]

    # 6.4 °C = 43.52 °F; 4.6 m/s = 10.29 mph
    assert selected == {
        "label": "New York, US",
        "lat": 40.7484,
        "lon": -73.9967,
        "temp": 43.5,
        "unit": "°F",
        "emoji": "☁️",
        "description": "broken clouds",
        "humidity": 62,
        "wind": 10.3,
        "speed_unit": "mph",
    }


@pytest.mark.django_db
def test_favorite_markers_show_only_the_current_users_favorites(
    client, mocked_responses
):
    # Every weather call returns the New York fixture; only the labels matter here.
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    alice = UserFactory()
    FavoriteFactory(user=alice, name="London", state="England", country="GB")
    FavoriteFactory(user=alice, name="Paris", state="", country="FR")
    FavoriteFactory(name="Tokyo", state="", country="JP")  # another user's

    client.force_login(alice)
    favorites = map_data(get_panel(client))["favorites"]

    assert [marker["label"] for marker in favorites] == [
        "London, England, GB",
        "Paris, FR",
    ]

    client.logout()
    assert map_data(get_panel(client))["favorites"] == []


def mock_weather_at(mocked_responses, lat, lon, **kwargs):
    """Mock /data/2.5/weather for one pair of coordinates."""
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "appid": "test-openweather-key",
    }
    mocked_responses.get(
        WEATHER_URL, match=[matchers.query_param_matcher(params)], **kwargs
    )


@pytest.mark.django_db
def test_one_failing_favorite_does_not_break_the_map(mocked_responses):
    # Report a crash as a 500 status instead of raising it in the test.
    client = Client(raise_request_exception=False)
    new_york = load_fixture("weather_new_york.json")
    mock_weather_at(mocked_responses, "40.7484", "-73.9967", json=new_york)
    mock_weather_at(mocked_responses, "51.5073", "-0.1276", status=500)
    mock_weather_at(mocked_responses, "48.8566", "2.3522", json=new_york)
    alice = UserFactory()
    FavoriteFactory(user=alice, name="London", lat=51.5073, lon=-0.1276)
    FavoriteFactory(
        user=alice, name="Paris", state="", country="FR", lat=48.8566, lon=2.3522
    )
    client.force_login(alice)

    response = get_panel(client)

    assert response.status_code == 200
    data = map_data(response)
    assert data["selected"]["temp"] == 6.4
    london, paris = data["favorites"]
    # London still gets a marker, just without weather.
    assert london == {
        "label": "London, England, GB",
        "lat": 51.5073,
        "lon": -0.1276,
        "temp": None,
    }
    assert paris["label"] == "Paris, FR"
    assert paris["temp"] == 6.4


@pytest.mark.django_db
def test_full_page_loads_leaflet_and_the_map_initializer(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = client.get(reverse("weather"), NEW_YORK)

    assertContains(response, "leaflet@1.9.4/dist/leaflet.js")
    assertContains(response, "leaflet@1.9.4/dist/leaflet.css")
    assertContains(response, "<div data-weather-map")
    assertContains(response, "tile.openstreetmap.org")
    # The same initializer runs on load and after every HTMX swap.
    assertContains(response, '"DOMContentLoaded", drawWeatherMap')
    assertContains(response, '"htmx:afterSettle", drawWeatherMap')


@pytest.mark.django_db
def test_no_map_without_weather(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, status=500)
    FavoriteFactory(user=(user := UserFactory()))
    client.force_login(user)

    response = get_panel(client)

    assertNotContains(response, "<div data-weather-map")
    assertNotContains(response, 'id="weather-map-data"')
    assert len(mocked_responses.calls) == 1  # no weather fetched for favorites


@pytest.mark.django_db
def test_favorite_at_the_selected_place_is_not_drawn_twice(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    alice = UserFactory()
    FavoriteFactory(user=alice, name="New York", lat=40.7484, lon=-73.9967)
    FavoriteFactory(user=alice, name="London", lat=51.5073, lon=-0.1276)
    client.force_login(alice)

    # The selected coordinates round to the New York favorite's.
    favorites = map_data(
        get_panel(client, {**NEW_YORK, "lat": "40.74841", "lon": "-73.99669"})
    )["favorites"]

    assert [marker["label"] for marker in favorites] == ["London, England, GB"]


@pytest.mark.django_db
def test_favorite_weather_is_cached_and_never_leaks_the_api_key(
    client, mocked_responses
):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    # Mock the forecast too: a failed forecast is not cached and is retried.
    mocked_responses.get(FORECAST_URL, json=load_fixture("forecast_new_york.json"))
    alice = UserFactory()
    FavoriteFactory(user=alice, name="London", lat=51.5073, lon=-0.1276)
    client.force_login(alice)

    first = get_panel(client)
    calls_after_first = len(mocked_responses.calls)
    second = client.get(reverse("weather"), NEW_YORK)  # full page

    assert len(mocked_responses.calls) == calls_after_first
    for response in (first, second):
        assertNotContains(response, "test-openweather-key")
        assertNotContains(response, "openweathermap.org")
