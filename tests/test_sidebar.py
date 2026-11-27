"""Tests for the favorites sidebar: sliding in and out, and how it looks."""

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

from tests.factories import FavoriteFactory, UserFactory
from tests.openweather import GEO_REVERSE_URL, WEATHER_URL, load_fixture
from weather.services import Place

HTMX = {"HX-Request": "true"}

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


# --- How the sidebar looks ----------------------------------------------------


@pytest.mark.parametrize(
    ("state", "country", "region"),
    [("England", "GB", "England, GB"), ("", "NO", "NO"), ("", "", "")],
)
def test_place_region_joins_state_and_country(state, country, region):
    assert Place("City", state, country, 0.0, 0.0).region == region


def sidebar_for(client, user):
    """GET the user's favorites list partial the way HTMX does."""
    client.force_login(user)
    return client.get(reverse("favorites"), headers=HTMX)


@pytest.mark.django_db
def test_favorite_rows_show_the_name_over_the_region(client):
    user = UserFactory()
    FavoriteFactory(user=user, name="London", state="England", country="GB")

    response = sidebar_for(client, user)

    assertContains(response, 'class="block truncate font-semibold">London</span>')
    assertContains(response, ">England, GB</span>")


@pytest.mark.django_db
def test_default_favorite_is_listed_first(client):
    user = UserFactory()
    FavoriteFactory(user=user, name="Paris")
    FavoriteFactory(user=user, name="Oslo", is_default=True)

    html = sidebar_for(client, user).content.decode()

    assert html.index(">Oslo</span>") < html.index(">Paris</span>")


@pytest.mark.django_db
def test_sidebar_header_counts_the_favorites(client):
    user = UserFactory()
    FavoriteFactory.create_batch(2, user=user)
    client.force_login(user)

    response = client.get(reverse("dashboard"))

    assertContains(response, 'data-favorites-count class="badge badge-sm">2</span>')


@pytest.mark.django_db
def test_sidebar_header_count_is_hidden_without_favorites(client):
    client.force_login(UserFactory())

    response = client.get(reverse("dashboard"))

    assertContains(response, 'data-favorites-count class="badge badge-sm hidden">0<')


@pytest.mark.django_db
def test_empty_favorites_explain_how_to_add_one(client):
    response = sidebar_for(client, UserFactory())

    assertContains(response, "⭐")
    assertContains(response, "tap ☆ Save to keep it here")


@pytest.mark.django_db
def test_logged_out_sidebar_has_a_log_in_button(client):
    response = client.get(reverse("dashboard"))

    assertContains(response, 'href="/accounts/login/?next=/" class="btn btn-primary')
    assertContains(response, "to save places")


@pytest.mark.django_db
def test_weather_badge_is_a_chip_colored_by_the_weather(client, mocked_responses):
    # Fixture: broken clouds, so the "clouds" theme.
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = client.get(
        reverse("weather_badge"), {"lat": "40.7484", "lon": "-73.9967"}, headers=HTMX
    )

    assertContains(response, 'data-weather-theme="clouds"')
    assertContains(response, "from-slate-300 to-slate-500")
    assertContains(response, "☁️ 6°C")
