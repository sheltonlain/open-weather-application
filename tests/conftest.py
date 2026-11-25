"""Shared pytest fixtures for the whole suite."""

import pytest
import responses
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Start and end every test with an empty cache."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def mocked_responses():
    """Block real HTTP: any request without a registered mock raises an error.

    Tests register expected OpenWeather calls on this fixture, e.g.
    ``mocked_responses.get(url, json=...)``.
    """
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps
