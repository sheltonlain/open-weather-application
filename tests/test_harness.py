"""Tests that the test harness itself keeps the suite offline and isolated."""

import pytest
import requests
from django.conf import settings
from django.core.cache import cache


def test_unmocked_http_call_fails():
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get("https://api.openweathermap.org/data/2.5/weather", timeout=5)


def test_tests_use_fake_api_key():
    assert settings.OPENWEATHER_API_KEY == "test-openweather-key"


def test_cache_starts_empty_part_one():
    assert cache.get("leftover") is None
    cache.set("leftover", "value")


def test_cache_starts_empty_part_two():
    assert cache.get("leftover") is None
