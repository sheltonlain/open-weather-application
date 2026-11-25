"""Tests that HTMX requests carry a valid CSRF token."""

import json
import re

import pytest
from django.test import Client


@pytest.mark.django_db
def test_page_csrf_header_for_htmx_is_accepted():
    client = Client(enforce_csrf_checks=True)
    page = client.get("/").content.decode()

    match = re.search(r"hx-headers='([^']*)'", page)
    assert match is not None, "base.html should set hx-headers"
    headers = json.loads(match.group(1))

    response = client.post(
        "/", headers={"HX-Request": "true", "X-CSRFToken": headers["X-CSRFToken"]}
    )
    assert response.status_code != 403
