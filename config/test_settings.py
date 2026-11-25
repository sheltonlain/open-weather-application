"""Settings for the test suite: fake secrets, never the real ones."""

import os

# Provide placeholders so settings import even without a .env file.
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("OPENWEATHER_API_KEY", "test-openweather-key")

from config.settings import *  # noqa: E402, F403

# Always override, so tests never see the real key even if .env is present.
SECRET_KEY = "test-secret-key"
OPENWEATHER_API_KEY = "test-openweather-key"

# Fast password hashing for tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
