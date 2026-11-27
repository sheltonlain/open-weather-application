"""Tests for the current weather panel (GET /weather/?lat=&lon=)."""

import pytest
import requests
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertTemplateNotUsed,
    assertTemplateUsed,
)
from responses import matchers

from tests.openweather import (
    GEO_DIRECT_URL,
    GEO_REVERSE_URL,
    WEATHER_URL,
    load_fixture,
)

NEW_YORK = {"lat": "40.7484", "lon": "-73.9967"}


def get_panel(client, params):
    """GET the weather panel partial the way HTMX does."""
    return client.get(reverse("weather"), params, headers={"HX-Request": "true"})


@pytest.mark.django_db
def test_sunrise_and_sunset_are_shown_in_local_time(client, mocked_responses):
    # Fixture: sunrise 11:55 UTC, sunset 21:31 UTC, timezone offset -5 hours.
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = get_panel(client, NEW_YORK)

    assertContains(response, "06:55")
    assertContains(response, "16:31")
    assertNotContains(response, "11:55")
    assertNotContains(response, "21:31")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "params",
    [
        pytest.param({}, id="missing-both"),
        pytest.param({"lat": "40.7484"}, id="missing-lon"),
        pytest.param({"lat": "abc", "lon": "-73.9967"}, id="non-numeric"),
        pytest.param({"lat": "nan", "lon": "-73.9967"}, id="nan"),
        pytest.param({"lat": "91", "lon": "0"}, id="lat-out-of-range"),
        pytest.param({"lat": "0", "lon": "-181"}, id="lon-out-of-range"),
    ],
)
def test_missing_or_invalid_coordinates_return_400(client, mocked_responses, params):
    response = get_panel(client, params)

    assert response.status_code == 400
    assert len(mocked_responses.calls) == 0


@pytest.mark.django_db
def test_panel_shows_every_current_metric(client, mocked_responses):
    mocked_responses.get(
        WEATHER_URL,
        json=load_fixture("weather_new_york.json"),
        match=[
            matchers.query_param_matcher(
                {**NEW_YORK, "units": "metric", "appid": "test-openweather-key"}
            )
        ],
    )

    response = get_panel(client, NEW_YORK)

    assert response.status_code == 200
    for text in [
        "broken clouds",
        "☁️",  # icon 04d
        "6°C",  # temperature 6.4
        "Feels like",
        "3°C",  # feels like 3.1
        "62%",  # humidity
        "4.6 m/s",  # wind
        "75%",  # cloudiness
        "1018 hPa",  # pressure
        "Sunrise",
        "Sunset",
    ]:
        assertContains(response, text)


@pytest.mark.django_db
def test_service_failure_shows_friendly_message(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, status=500)

    response = get_panel(client, NEW_YORK)

    assert response.status_code == 200
    assertContains(response, "Weather is unavailable right now. Please try again.")


@pytest.mark.django_db
def test_htmx_request_returns_partial_only(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = get_panel(client, NEW_YORK)

    assertTemplateUsed(response, "weather/partials/weather_panel.html")
    assertTemplateNotUsed(response, "base.html")


@pytest.mark.django_db
def test_normal_request_returns_full_page(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = client.get(reverse("weather"), NEW_YORK)

    assert response.status_code == 200
    assertTemplateUsed(response, "weather/partials/weather_panel.html")
    assertTemplateUsed(response, "base.html")


@pytest.mark.django_db
def test_invalid_coordinates_full_page_explains_the_error(client):
    response = client.get(reverse("weather"), {"lat": "abc", "lon": "0"})

    assert response.status_code == 400
    assertTemplateUsed(response, "base.html")
    assertContains(response, "That location is not valid", status_code=400)


@pytest.mark.django_db
def test_panel_never_exposes_api_key(client, mocked_responses, settings):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    for response in (
        get_panel(client, NEW_YORK),
        client.get(reverse("weather"), NEW_YORK),
        client.get(reverse("dashboard")),
    ):
        assertNotContains(response, settings.OPENWEATHER_API_KEY)
        assertNotContains(response, "openweathermap.org")


@pytest.mark.django_db
def test_dashboard_shows_empty_weather_panel(client):
    response = client.get(reverse("dashboard"))

    assertContains(response, 'id="weather-panel"')
    assertContains(response, "Pick a place to see its weather.")


@pytest.mark.django_db
def test_search_result_loads_weather_panel_via_htmx(client, mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=load_fixture("geo_direct_paris_tx.json"))
    place = load_fixture("geo_direct_paris_tx.json")[0]

    response = client.get(
        reverse("search"), {"q": "Paris, TX"}, headers={"HX-Request": "true"}
    )

    url = (
        f"{reverse('weather')}?lat={place['lat']}&amp;lon={place['lon']}"
        "&amp;name=Paris&amp;state=Texas&amp;country=US"
    )
    assertContains(response, f'hx-get="{url}"')
    assertContains(response, f'href="{url}"')
    assertContains(response, 'hx-target="#weather-panel"')


@pytest.mark.django_db
def test_panel_shows_the_chosen_place_name_not_the_station_name(
    client, mocked_responses
):
    # OpenWeather labels these coordinates with its nearest station, Weehawken.
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = get_panel(client, {**NEW_YORK, "name": "New York", "country": "US"})

    assertContains(response, "New York, US")
    assertNotContains(response, "Weehawken")


@pytest.mark.django_db
def test_panel_without_a_name_shows_the_reverse_geocoded_name(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    mocked_responses.get(
        GEO_REVERSE_URL,
        json=load_fixture("geo_reverse_new_york.json"),
        match=[
            matchers.query_param_matcher(
                {**NEW_YORK, "limit": "1", "appid": "test-openweather-key"}
            )
        ],
    )

    response = get_panel(client, NEW_YORK)

    assertContains(response, "New York, New York, US")
    assertNotContains(response, "Weehawken")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "reverse_response",
    [
        pytest.param({"body": requests.exceptions.Timeout()}, id="timeout"),
        pytest.param({"status": 500}, id="server-error"),
        pytest.param({"json": []}, id="no-place-found"),
    ],
)
def test_reverse_geocode_failure_labels_weather_with_coordinates(
    client, mocked_responses, reverse_response
):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    mocked_responses.get(GEO_REVERSE_URL, **reverse_response)

    response = get_panel(client, NEW_YORK)

    assert response.status_code == 200
    assertContains(response, "6°C")  # the weather still shows
    assertContains(response, "40.7484, -73.9967")
    assertNotContains(response, "Weehawken")
