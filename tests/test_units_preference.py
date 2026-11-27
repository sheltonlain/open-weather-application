"""Tests for showing weather in the active unit system (metric or imperial)."""

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertTemplateNotUsed,
    assertTemplateUsed,
)

from tests.factories import UserFactory
from tests.openweather import WEATHER_URL, load_fixture

NEW_YORK = {"lat": "40.7484", "lon": "-73.9967"}


def get_panel(client):
    """GET the New York weather panel partial the way HTMX does."""
    return client.get(reverse("weather"), NEW_YORK, headers={"HX-Request": "true"})


def use_imperial_logged_in(client):
    client.force_login(UserFactory(units="imperial"))


def use_imperial_anonymous(client):
    session = client.session
    session["units"] = "imperial"
    session.save()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "use_imperial",
    [
        pytest.param(use_imperial_logged_in, id="logged-in-user-setting"),
        pytest.param(use_imperial_anonymous, id="anonymous-session"),
    ],
)
def test_panel_shows_imperial_values_and_labels(client, mocked_responses, use_imperial):
    # Fixture (metric): temp 6.4 °C, feels like 3.1 °C, wind 4.6 m/s.
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    use_imperial(client)

    response = get_panel(client)

    assertContains(response, "44°F")  # 43.52 °F
    assertContains(response, "38°F")  # 37.58 °F
    assertContains(response, "10.3 mph")  # 10.29 mph
    assertNotContains(response, "°C")
    assertNotContains(response, "m/s")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login",
    [
        pytest.param(lambda client: None, id="anonymous-default"),
        pytest.param(
            lambda client: client.force_login(UserFactory(units="metric")),
            id="logged-in-metric",
        ),
    ],
)
def test_panel_shows_metric_values_and_labels(client, mocked_responses, login):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    login(client)

    response = get_panel(client)

    assertContains(response, "6°C")
    assertContains(response, "3°C")
    assertContains(response, "4.6 m/s")
    assertNotContains(response, "°F")
    assertNotContains(response, "mph")


def switch_to_imperial(client):
    """POST the units toggle the way HTMX does."""
    return client.post(
        reverse("set_units"), {"units": "imperial"}, headers={"HX-Request": "true"}
    )


@pytest.mark.django_db
def test_logged_in_switch_persists_and_reuses_cached_weather(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    user = UserFactory(units="metric")
    client.force_login(user)
    assertContains(get_panel(client), "6°C")

    switch_to_imperial(client)

    user.refresh_from_db()
    assert user.units == "imperial"
    assertContains(get_panel(client), "44°F")
    assert len(mocked_responses.calls) == 1  # second panel came from the cache


@pytest.mark.django_db
def test_anonymous_switch_is_stored_in_session_and_reuses_cached_weather(
    client, mocked_responses
):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    assertContains(get_panel(client), "6°C")

    switch_to_imperial(client)

    assert client.session.get("units") == "imperial"
    assertContains(get_panel(client), "44°F")
    assert len(mocked_responses.calls) == 1  # second panel came from the cache


# The units endpoint


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["", "kelvin", "IMPERIAL"])
def test_unknown_units_are_rejected(client, value):
    user = UserFactory(units="metric")
    client.force_login(user)

    response = client.post(reverse("set_units"), {"units": value})

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.units == "metric"


@pytest.mark.django_db
def test_unknown_units_are_not_stored_for_anonymous_visitor(client):
    response = client.post(reverse("set_units"), {"units": "kelvin"})

    assert response.status_code == 400
    assert "units" not in client.session


@pytest.mark.django_db
def test_units_endpoint_only_accepts_post(client):
    response = client.get(reverse("set_units"), {"units": "imperial"})

    assert response.status_code == 405


@pytest.mark.django_db
def test_units_endpoint_requires_csrf_token():
    client = Client(enforce_csrf_checks=True)

    response = client.post(reverse("set_units"), {"units": "imperial"})

    assert response.status_code == 403
    assert "units" not in client.session


@pytest.mark.django_db
def test_htmx_switch_rerenders_toggle_and_signals_the_panel(client):
    response = switch_to_imperial(client)

    assert response.status_code == 200
    assert response["HX-Trigger"] == "unitsChanged"
    assertTemplateUsed(response, "accounts/partials/units_toggle.html")
    assertTemplateNotUsed(response, "base.html")
    assertContains(response, 'value="imperial"')
    assert "btn-active" in active_button(response.content.decode(), "imperial")


@pytest.mark.django_db
def test_normal_switch_redirects_back(client):
    response = client.post(
        reverse("set_units"),
        {"units": "imperial", "next": "/weather/?lat=1&lon=2"},
        follow=True,
    )

    assert response.redirect_chain[0] == ("/weather/?lat=1&lon=2", 302)


@pytest.mark.django_db
def test_normal_switch_shows_saved_message(client):
    client.force_login(UserFactory())

    response = client.post(
        reverse("set_units"),
        {"units": "imperial", "next": reverse("settings")},
        follow=True,
    )

    assertContains(response, "Units saved.")


@pytest.mark.django_db
@pytest.mark.parametrize("next_url", ["", "https://evil.example/", "//evil.example/"])
def test_normal_switch_never_redirects_off_site(client, next_url):
    response = client.post(
        reverse("set_units"), {"units": "imperial", "next": next_url}
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard")


# Header toggle, panel reload, settings page


def active_button(html, value):
    """Return the <button> tag in the units toggle for the given value."""
    start = html.index(f'value="{value}"')
    return html[html.rindex("<button", 0, start) : html.index(">", start)]


@pytest.mark.django_db
def test_header_toggle_highlights_the_active_units(client):
    use_imperial_anonymous(client)

    html = client.get(reverse("dashboard")).content.decode()

    assert 'id="units-toggle"' in html
    assert "btn-active" in active_button(html, "imperial")
    assert "btn-active" not in active_button(html, "metric")


@pytest.mark.django_db
def test_panel_reloads_itself_when_units_change(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = get_panel(client)

    assertContains(response, 'hx-trigger="unitsChanged from:body"')
    assertContains(response, 'hx-get="/weather/?lat=40.7484&amp;lon=-73.9967"')


@pytest.mark.django_db
def test_settings_page_requires_login(client):
    response = client.get(reverse("settings"))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


@pytest.mark.django_db
def test_settings_page_shows_the_saved_choice(client):
    client.force_login(UserFactory(units="imperial"))

    response = client.get(reverse("settings"))

    assert response.status_code == 200
    html = response.content.decode()
    radio = 'type="radio" name="units" value="{}"'
    assert "checked" in html[html.index(radio.format("imperial")) :].split(">")[0]
    assert "checked" not in html[html.index(radio.format("metric")) :].split(">")[0]
    assertContains(response, "Imperial (°F, mph)")


@pytest.mark.django_db
def test_settings_form_saves_units(client):
    user = UserFactory(units="metric")
    client.force_login(user)

    response = client.post(
        reverse("set_units"), {"units": "imperial", "next": reverse("settings")}
    )

    assert response["Location"] == reverse("settings")
    user.refresh_from_db()
    assert user.units == "imperial"


@pytest.mark.django_db
def test_header_links_to_settings_for_logged_in_users_only(client):
    assertNotContains(client.get(reverse("dashboard")), reverse("settings"))

    client.force_login(UserFactory())

    assertContains(client.get(reverse("dashboard")), reverse("settings"))
