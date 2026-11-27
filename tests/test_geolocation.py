"""Tests for the dashboard's geolocation setup and its fallback."""

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from tests.factories import FavoriteFactory, UserFactory


@pytest.mark.django_db
def test_geolocation_falls_back_to_the_first_favorite_only_when_there_is_one(
    client, mocked_responses
):
    alice = UserFactory()
    first = FavoriteFactory(user=alice, name="Paris", state="", country="FR")
    FavoriteFactory(user=alice, name="London")
    bob = UserFactory()  # logged in, but no favorites

    client.force_login(alice)
    alice_page = client.get(reverse("dashboard"))
    client.force_login(bob)
    bob_page = client.get(reverse("dashboard"))
    client.logout()
    anonymous_page = client.get(reverse("dashboard"))

    query = first.place.query_string.replace("&", "&amp;")
    assertContains(alice_page, f'data-fallback-url="{reverse("weather")}?{query}"')
    for page in (bob_page, anonymous_page):
        assertContains(page, "data-geolocation")
        assertNotContains(page, "data-fallback-url")
    # The fallback is only a link: the dashboard itself calls no weather API.
    assert len(mocked_responses.calls) == 0
