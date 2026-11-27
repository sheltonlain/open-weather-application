"""Tests for the 5-day forecast (service grouping, chart data, panel)."""

import json
import re
from datetime import date

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from tests.factories import UserFactory
from tests.openweather import FORECAST_URL, WEATHER_URL, load_fixture
from weather.services import DailyForecast, get_daily_forecast

NEW_YORK = (40.7484, -73.9967)
DAY_LABELS = ["Thu 26 Nov", "Fri 27 Nov", "Sat 28 Nov", "Sun 29 Nov", "Mon 30 Nov"]


def test_forecast_steps_are_grouped_into_five_daily_summaries(mocked_responses):
    mocked_responses.get(FORECAST_URL, json=load_fixture("forecast_new_york.json"))

    days = get_daily_forecast(*NEW_YORK)

    # The fixture starts at 10:00 local on 26 Nov; the partial 6th day is dropped.
    # A day's icon is its daytime variant, even if the first match was at night.
    assert days == [
        DailyForecast(date(2026, 11, 26), 7.8, 2.4, "broken clouds", "04d"),
        DailyForecast(date(2026, 11, 27), 8.3, 0.8, "clear sky", "01d"),
        DailyForecast(date(2026, 11, 28), 6.0, 1.2, "light rain", "10d"),
        DailyForecast(date(2026, 11, 29), 4.4, 1.4, "light snow", "13d"),
        DailyForecast(date(2026, 11, 30), 3.5, -1.2, "clear sky", "01d"),
    ]


def forecast_step(timestamp: int, temp: float) -> dict:
    """Build one minimal 3-hour forecast step."""
    return {
        "dt": timestamp,
        "main": {"temp": temp},
        "weather": [{"description": "clear sky", "icon": "01n"}],
    }


def test_days_are_grouped_by_local_date_not_utc(mocked_responses):
    # New York is UTC-5. 03:00 UTC on 27 Nov is still 22:00 on 26 Nov locally.
    mocked_responses.get(
        FORECAST_URL,
        json={
            "city": {"timezone": -18000},
            "list": [
                forecast_step(1795705200, 4.0),  # 26 Nov 15:00 UTC = 10:00 local
                forecast_step(1795737600, -3.0),  # 27 Nov 00:00 UTC = 19:00 local
                forecast_step(1795748400, 1.0),  # 27 Nov 03:00 UTC = 22:00 local
                forecast_step(1795759200, 6.0),  # 27 Nov 06:00 UTC = 01:00 local
            ],
        },
    )

    days = get_daily_forecast(*NEW_YORK)

    assert [(d.date, d.high, d.low) for d in days] == [
        (date(2026, 11, 26), 4.0, -3.0),
        (date(2026, 11, 27), 6.0, 6.0),
    ]


@pytest.mark.django_db
def test_forecast_failure_still_shows_current_conditions(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    mocked_responses.get(FORECAST_URL, status=500)

    response = client.get(
        reverse("weather"),
        {"lat": NEW_YORK[0], "lon": NEW_YORK[1]},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assertContains(response, "broken clouds")  # current conditions
    assertContains(response, "1018 hPa")
    assertContains(response, "Forecast is unavailable right now. Please try again.")


def mock_new_york(mocked_responses):
    """Register the New York current weather and forecast responses."""
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    mocked_responses.get(FORECAST_URL, json=load_fixture("forecast_new_york.json"))


def get_panel(client, htmx=True):
    """GET the New York weather panel, as a partial or a full page."""
    headers = {"HX-Request": "true"} if htmx else {}
    params = {"lat": NEW_YORK[0], "lon": NEW_YORK[1]}
    return client.get(reverse("weather"), params, headers=headers)


def chart_data(response) -> dict:
    """Return the forecast chart data emitted by the json_script tag."""
    match = re.search(
        r'<script id="forecast-chart-data" type="application/json">(.*?)</script>',
        response.content.decode(),
    )
    assert match, "forecast chart data not found"
    return json.loads(match.group(1))


@pytest.mark.django_db
def test_chart_data_is_emitted_in_metric_by_default(client, mocked_responses):
    mock_new_york(mocked_responses)

    data = chart_data(get_panel(client))

    assert data == {
        "labels": DAY_LABELS,
        "highs": [7.8, 8.3, 6.0, 4.4, 3.5],
        "lows": [2.4, 0.8, 1.2, 1.4, -1.2],
        "conditions": [
            "broken clouds",
            "clear sky",
            "light rain",
            "light snow",
            "clear sky",
        ],
        "unit": "°C",
    }


@pytest.mark.django_db
def test_chart_data_and_day_cards_use_imperial_for_imperial_users(
    client, mocked_responses
):
    mock_new_york(mocked_responses)
    client.force_login(UserFactory(units="imperial"))

    response = get_panel(client)
    data = chart_data(response)

    # 7.8 °C = 46.04 °F, 2.4 °C = 36.32 °F, -1.2 °C = 29.84 °F
    assert data["unit"] == "°F"
    assert data["highs"][0] == 46.0
    assert data["lows"][0] == 36.3
    assert data["lows"][4] == 29.8
    assertContains(response, "46°F")  # first day card high
    assertNotContains(response, "°C")


@pytest.mark.django_db
def test_forecast_shows_five_day_cards(client, mocked_responses):
    mock_new_york(mocked_responses)

    response = get_panel(client)

    assertContains(response, "5-day forecast")
    for label in DAY_LABELS:
        assertContains(response, label)
    assertNotContains(response, "Tue 1 Dec")  # partial 6th day is dropped
    assertContains(response, 'id="forecast-chart"')


@pytest.mark.django_db
def test_full_page_loads_chart_js_and_its_initializer(client, mocked_responses):
    mock_new_york(mocked_responses)

    response = get_panel(client, htmx=False)

    assertContains(response, "chart.js@4.4.1/dist/chart.umd.min.js")
    assertContains(response, 'id="forecast-chart-data"')
    # The same initializer runs on load and after every HTMX swap.
    assertContains(response, '"DOMContentLoaded", drawForecastChart')
    assertContains(response, '"htmx:afterSettle", drawForecastChart')


@pytest.mark.django_db
def test_forecast_uses_the_cache_and_never_leaks_the_api_key(client, mocked_responses):
    mock_new_york(mocked_responses)

    first = get_panel(client)
    second = get_panel(client, htmx=False)

    assert len(mocked_responses.calls) == 2  # one weather + one forecast call
    for response in (first, second):
        assertNotContains(response, "test-openweather-key")
        assertNotContains(response, "openweathermap.org")
