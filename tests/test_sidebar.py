"""Tests for the favorites sidebar that slides in and out on wide screens."""

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

from tests.openweather import GEO_REVERSE_URL, WEATHER_URL, load_fixture

SIDEBAR_PAGES = [
    pytest.param(lambda: reverse("dashboard"), id="dashboard"),
    pytest.param(lambda: reverse("search"), id="search"),
    pytest.param(
        lambda: reverse("weather") + "?lat=40.7484&lon=-73.9967", id="weather"
    ),
]


@pytest.fixture
def new_york_weather(mocked_responses):
    """Mock the calls a full weather page makes for New York."""
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    mocked_responses.get(GEO_REVERSE_URL, json=[])


@pytest.mark.django_db
@pytest.mark.parametrize("url", SIDEBAR_PAGES)
def test_pages_with_favorites_share_the_sliding_sidebar_layout(
    client, new_york_weather, url
):
    response = client.get(url())

    assertTemplateUsed(response, "favorites/sidebar_layout.html")
    assertContains(response, 'id="favorites"', count=1)
    html = response.content.decode()
    sidebar = html[html.index('id="favorites"') : html.index("</aside>")]
    assert sidebar.count("data-sidebar-toggle") == 1


@pytest.mark.django_db
def test_sidebar_toggle_starts_open_and_names_what_it_controls(client):
    html = client.get(reverse("dashboard")).content.decode()

    start = html.index("<button", html.index('id="favorites"'))
    toggle = html[start : html.index(">", start)]
    assert "data-sidebar-toggle" in toggle
    assert 'aria-controls="favorites-body"' in toggle
    assert 'aria-expanded="true"' in toggle
    assert 'aria-label="Hide favorites"' in toggle
    assert 'id="favorites-body"' in html


@pytest.mark.django_db
def test_sidebar_toggle_has_a_visible_show_favorites_label(client):
    html = client.get(reverse("dashboard")).content.decode()

    start = html.index("data-sidebar-toggle")
    button = html[start : html.index("</button>", start)]
    assert ">Show favorites</span>" in button
