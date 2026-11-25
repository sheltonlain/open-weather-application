"""Tests for parse_query(), which decides whether a search is a city or a ZIP."""

import pytest

from weather.queries import ParsedQuery, parse_query


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("London", ParsedQuery("city", "London"), id="city"),
        pytest.param("  Paris  ", ParsedQuery("city", "Paris"), id="city-whitespace"),
        pytest.param("Paris,FR", ParsedQuery("city", "Paris,FR"), id="city-country"),
        pytest.param("10001", ParsedQuery("zip", "10001,US"), id="bare-zip-to-us"),
        pytest.param("10001,US", ParsedQuery("zip", "10001,US"), id="zip-country"),
        pytest.param(
            "75001,FR", ParsedQuery("zip", "75001,FR"), id="zip-other-country"
        ),
        pytest.param(
            " 10001 , us ", ParsedQuery("zip", "10001,US"), id="zip-whitespace-case"
        ),
        pytest.param(
            "SW1A 1AA,GB", ParsedQuery("zip", "SW1A 1AA,GB"), id="letter-first-zip"
        ),
        pytest.param(
            "SW1A 1AA", ParsedQuery("city", "SW1A 1AA"), id="letter-first-no-country"
        ),
    ],
)
def test_parse_query(raw, expected):
    assert parse_query(raw) == expected
