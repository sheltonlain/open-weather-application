"""Tests for the custom user model."""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model


def test_auth_user_model_is_custom_user():
    assert settings.AUTH_USER_MODEL == "accounts.User"


@pytest.mark.django_db
def test_new_user_defaults_to_metric_units():
    user = get_user_model().objects.create_user(username="ana", password="pw")

    assert user.units == "metric"
