"""Tests for the small weather badge shown next to each favorite."""

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains

from tests.factories import FavoriteFactory, UserFactory
from tests.openweather import WEATHER_URL, load_fixture

HTMX = {"HX-Request": "true"}
NEW_YORK = {"lat": "40.7484", "lon": "-73.9967"}


def get_badge(client, params):
    """GET the weather badge partial the way HTMX does."""
    return client.get(reverse("weather_badge"), params, headers=HTMX)


@pytest.mark.django_db
def test_badge_shows_emoji_and_rounded_temperature(client, mocked_responses):
    # Fixture: 6.4 °C, broken clouds.
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = get_badge(client, NEW_YORK)

    assert response.status_code == 200
    assertContains(response, "☁️ 6°C")


@pytest.mark.django_db
def test_badge_uses_the_users_units(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    client.force_login(UserFactory(units="imperial"))

    response = get_badge(client, NEW_YORK)

    assertContains(response, "☁️ 44°F")  # 6.4 °C = 43.5 °F


@pytest.mark.django_db
def test_badge_with_invalid_coordinates_returns_400(client, mocked_responses):
    response = get_badge(client, {"lat": "abc", "lon": "0"})

    assert response.status_code == 400
    assert len(mocked_responses.calls) == 0


@pytest.mark.django_db
def test_badge_shows_a_dash_when_weather_is_unavailable(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, status=500)

    response = get_badge(client, NEW_YORK)

    assert response.status_code == 200
    assertContains(response, 'title="Weather unavailable"')


@pytest.mark.django_db
def test_each_favorite_loads_its_badge_and_reloads_on_units_change(client):
    user = UserFactory()
    FavoriteFactory(user=user, lat=40.7484, lon=-73.9967)
    client.force_login(user)

    response = client.get(reverse("favorites"), headers=HTMX)

    url = f"{reverse('weather_badge')}?lat=40.7484&amp;lon=-73.9967"
    assertContains(response, f'hx-get="{url}"')
    assertContains(response, 'hx-trigger="load, unitsChanged from:body"')
