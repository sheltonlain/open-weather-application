"""Helpers for reading required settings from the environment."""

import os

from django.core.exceptions import ImproperlyConfigured


def require_env(name: str) -> str:
    """Return the environment variable ``name`` or fail loudly if it is unset."""
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f"Missing required environment variable {name}. "
            "Add it to the .env file at the project root (see .env.example)."
        )
    return value
