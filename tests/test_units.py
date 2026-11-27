"""Tests for the pure metric-to-imperial conversion helpers."""

import pytest

from weather.units import celsius_to_fahrenheit, ms_to_mph


@pytest.mark.parametrize(
    ("celsius", "fahrenheit"),
    [
        pytest.param(0, 32, id="freezing"),
        pytest.param(100, 212, id="boiling"),
        pytest.param(-40, -40, id="scales-meet"),
        pytest.param(37, 98.6, id="body-temperature"),
        pytest.param(-17.5, 0.5, id="fractional-negative"),
    ],
)
def test_celsius_to_fahrenheit(celsius, fahrenheit):
    assert celsius_to_fahrenheit(celsius) == pytest.approx(fahrenheit)


@pytest.mark.parametrize(
    ("ms", "mph"),
    [
        pytest.param(0, 0, id="calm"),
        pytest.param(1, 2.236936, id="one-ms"),
        pytest.param(10, 22.36936, id="ten-ms"),
        pytest.param(4.47, 9.999, id="fractional"),
    ],
)
def test_ms_to_mph(ms, mph):
    assert ms_to_mph(ms) == pytest.approx(mph, abs=1e-3)
