"""Tests for the weather search view."""

import pytest
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertTemplateNotUsed,
    assertTemplateUsed,
)
from responses import matchers

from tests.openweather import GEO_DIRECT_URL, GEO_ZIP_URL, load_fixture
from weather.services import Place

LONDON = Place("London", "England", "GB", 51.5073219, -0.1276474)


@pytest.fixture
def fake_search(monkeypatch):
    """Replace the service so these tests only exercise the view."""
    monkeypatch.setattr("weather.views.search_cities", lambda query: [LONDON])


@pytest.mark.django_db
def test_search_htmx_request_returns_partial_only(client, fake_search):
    response = client.get(
        reverse("search"), {"q": "London"}, headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assertTemplateUsed(response, "weather/partials/search_results.html")
    assertTemplateNotUsed(response, "base.html")


@pytest.mark.django_db
def test_search_normal_request_returns_full_page(client, fake_search):
    response = client.get(reverse("search"), {"q": "London"})

    assert response.status_code == 200
    assertTemplateUsed(response, "weather/partials/search_results.html")
    assertTemplateUsed(response, "base.html")


# Rendering search results (real service, OpenWeather mocked with `responses`)


def search(client, query):
    """GET the search partial the way the dashboard's HTMX form does."""
    return client.get(reverse("search"), {"q": query}, headers={"HX-Request": "true"})


@pytest.mark.django_db
def test_search_results_list_name_state_and_country(client, mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=load_fixture("geo_direct_london.json"))

    response = search(client, "London")

    assertContains(response, "<li>", count=3)
    assertContains(response, "London, England, GB")
    assertContains(response, "London, Ontario, CA")
    assertContains(response, "London, Ohio, US")


@pytest.mark.django_db
def test_single_match_still_renders_as_list(client, mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=load_fixture("geo_direct_paris_tx.json"))

    response = search(client, "Paris, TX")

    assertContains(response, "<ul")
    assertContains(response, "<li>", count=1)
    assertContains(response, "Paris, Texas, US")


@pytest.mark.django_db
def test_place_without_state_omits_it(client, mocked_responses):
    mocked_responses.get(
        GEO_DIRECT_URL,
        json=[{"name": "Paris", "lat": 48.8588897, "lon": 2.320041, "country": "FR"}],
    )

    response = search(client, "Paris")

    assertContains(response, "Paris, FR")


@pytest.mark.django_db
def test_zip_search_uses_zip_geocoding_and_lists_one_place(client, mocked_responses):
    mocked_responses.get(
        GEO_ZIP_URL,
        json=load_fixture("geo_zip_10001.json"),
        match=[matchers.query_param_matcher({"zip": "10001,US"}, strict_match=False)],
    )

    response = search(client, "10001")

    assertContains(response, "<ul")
    assertContains(response, "<li>", count=1)
    assertContains(response, "New York, US")


@pytest.mark.django_db
def test_unknown_zip_shows_no_results_found(client, mocked_responses):
    mocked_responses.get(
        GEO_ZIP_URL, status=404, json={"cod": "404", "message": "not found"}
    )

    response = search(client, "00000")

    assert response.status_code == 200
    assertContains(response, "No results found")
    assertNotContains(response, "<li>")


@pytest.mark.django_db
def test_letter_first_postcode_with_country_uses_zip_geocoding(
    client, mocked_responses
):
    mocked_responses.get(
        GEO_ZIP_URL,
        json={
            "zip": "SW1A 1AA",
            "name": "London",
            "lat": 51.5010,
            "lon": -0.1416,
            "country": "GB",
        },
        match=[
            matchers.query_param_matcher({"zip": "SW1A 1AA,GB"}, strict_match=False)
        ],
    )

    response = search(client, "SW1A 1AA,GB")

    assertContains(response, "<li>", count=1)
    assertContains(response, "London, GB")


@pytest.mark.django_db
def test_no_matches_shows_no_results_found(client, mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=[])

    response = search(client, "Nowhereville")

    assert response.status_code == 200
    assertContains(response, "No results found")
    assertNotContains(response, "<li>")


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["", "   "])
def test_blank_query_shows_hint_without_calling_openweather(
    client, mocked_responses, query
):
    response = search(client, query)

    assert response.status_code == 200
    assertContains(response, "Type a city name or ZIP code to search")
    assert len(mocked_responses.calls) == 0


@pytest.mark.django_db
def test_missing_query_param_shows_hint(client):
    response = client.get(reverse("search"), headers={"HX-Request": "true"})

    assert response.status_code == 200
    assertContains(response, "Type a city name or ZIP code to search")


@pytest.mark.django_db
def test_service_failure_shows_friendly_message(client, mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, status=500)

    response = search(client, "London")

    assert response.status_code == 200
    assertContains(response, "Search is unavailable right now. Please try again.")


@pytest.mark.django_db
def test_search_never_exposes_api_key(client, mocked_responses, settings):
    mocked_responses.get(GEO_DIRECT_URL, json=load_fixture("geo_direct_london.json"))

    for response in (search(client, "London"), client.get(reverse("search"))):
        assertNotContains(response, settings.OPENWEATHER_API_KEY)


@pytest.mark.django_db
def test_query_is_kept_in_search_box_on_full_page(client, mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=[])

    response = client.get(reverse("search"), {"q": "Nowhereville"})

    assertContains(response, 'value="Nowhereville"')


# Search box on the dashboard


@pytest.mark.django_db
def test_dashboard_has_htmx_search_box(client):
    response = client.get(reverse("dashboard"))

    assertContains(response, f'hx-get="{reverse("search")}"')
    assertContains(response, 'hx-target="#search-results"')
    assertContains(response, 'name="q"')
    assertContains(response, 'id="search-results"')


@pytest.mark.django_db
def test_search_result_links_show_loading_and_clear_results(client, mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=load_fixture("geo_direct_london.json"))

    response = search(client, "London")

    # The weather panel dims while it loads, and the results list empties once
    # the chosen place's weather has loaded.
    assertContains(response, 'hx-indicator="#weather-panel"')
    assertContains(response, "hx-on::after-request=")
