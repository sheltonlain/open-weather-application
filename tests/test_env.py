"""Tests for loading required secrets from the environment."""

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import require_env


@pytest.mark.parametrize("name", ["SECRET_KEY", "OPENWEATHER_API_KEY"])
def test_missing_secret_fails_with_clear_error(monkeypatch, name):
    monkeypatch.delenv(name, raising=False)

    with pytest.raises(ImproperlyConfigured, match=name):
        require_env(name)
