"""Tests for the dashboard page at /."""

import pytest
from pytest_django.asserts import assertTemplateUsed


@pytest.mark.django_db
def test_dashboard_renders_shell_extending_base(client):
    response = client.get("/")

    assert response.status_code == 200
    assertTemplateUsed(response, "weather/dashboard.html")
    assertTemplateUsed(response, "base.html")
