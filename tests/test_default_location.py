"""Tests for choosing a favorite as the user's default location."""

import pytest
from django.db import IntegrityError
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from tests.factories import FavoriteFactory, UserFactory
from tests.openweather import WEATHER_URL, load_fixture

HTMX = {"HX-Request": "true"}


def default_url(favorite) -> str:
    """Return the URL that sets or clears a favorite as the default."""
    return reverse("default_favorite", args=[favorite.pk])


def panel_url(favorite) -> str:
    """Return a favorite's weather panel URL as it appears in HTML."""
    query = favorite.place.query_string.replace("&", "&amp;")
    return f"{reverse('weather')}?{query}"


@pytest.mark.django_db
def test_a_user_can_have_only_one_default():
    user = UserFactory()
    FavoriteFactory(user=user, is_default=True)

    with pytest.raises(IntegrityError):
        FavoriteFactory(user=user, is_default=True)


@pytest.mark.django_db
def test_setting_a_default_replaces_the_previous_one(client):
    user = UserFactory()
    old = FavoriteFactory(user=user, is_default=True)
    new = FavoriteFactory(user=user)
    client.force_login(user)

    response = client.post(default_url(new), headers=HTMX)

    assert response.status_code == 200
    assertContains(response, 'id="favorites-list"')
    old.refresh_from_db()
    new.refresh_from_db()
    assert not old.is_default
    assert new.is_default


@pytest.mark.django_db
def test_deleting_clears_the_default(client):
    user = UserFactory()
    favorite = FavoriteFactory(user=user, is_default=True)
    client.force_login(user)

    response = client.delete(default_url(favorite), headers=HTMX)

    assert response.status_code == 200
    favorite.refresh_from_db()
    assert not favorite.is_default


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["post", "delete"])
def test_another_users_favorite_cannot_be_made_default(client, method):
    favorite = FavoriteFactory()  # belongs to a different user
    client.force_login(UserFactory())

    response = getattr(client, method)(default_url(favorite), headers=HTMX)

    assert response.status_code == 404
    favorite.refresh_from_db()
    assert not favorite.is_default


@pytest.mark.django_db
def test_default_only_accepts_post_and_delete(client):
    user = UserFactory()
    favorite = FavoriteFactory(user=user)
    client.force_login(user)

    response = client.get(default_url(favorite), headers=HTMX)

    assert response.status_code == 405


@pytest.mark.django_db
def test_anonymous_htmx_request_is_sent_to_login(client):
    favorite = FavoriteFactory()

    response = client.post(default_url(favorite), headers=HTMX)

    assert response.headers["HX-Redirect"].startswith(reverse("login"))
    favorite.refresh_from_db()
    assert not favorite.is_default


@pytest.mark.django_db
def test_sidebar_shows_which_favorite_is_the_default(client):
    user = UserFactory()
    home = FavoriteFactory(user=user, name="Home", is_default=True)
    other = FavoriteFactory(user=user, name="Other")
    client.force_login(user)

    response = client.get(reverse("favorites"), headers=HTMX)

    # Clicking the current default clears it (DELETE); any other sets it (POST).
    assertContains(response, f'hx-delete="{default_url(home)}"')
    assertContains(response, f'hx-post="{default_url(other)}"')
    assertContains(response, 'aria-pressed="true"', count=1)
    assertContains(response, 'aria-pressed="false"', count=1)


@pytest.mark.django_db
def test_dashboard_opens_on_the_default_and_falls_back_to_it(client, mocked_responses):
    user = UserFactory()
    FavoriteFactory(user=user, name="First")
    home = FavoriteFactory(user=user, name="Home", is_default=True)
    client.force_login(user)

    response = client.get(reverse("dashboard"))

    assertContains(response, f'data-default-url="{panel_url(home)}"')
    assertContains(response, f'data-fallback-url="{panel_url(home)}"')
    assert len(mocked_responses.calls) == 0  # the browser loads it, not the page


@pytest.mark.django_db
def test_dashboard_without_a_default_has_no_default_url(client):
    user = UserFactory()
    FavoriteFactory(user=user)
    client.force_login(user)

    response = client.get(reverse("dashboard"))

    assertNotContains(response, "data-default-url")


@pytest.mark.django_db
def test_default_favorite_is_labeled_in_the_sidebar(client):
    user = UserFactory()
    FavoriteFactory(user=user, name="Home", is_default=True)
    FavoriteFactory(user=user, name="Other")
    client.force_login(user)

    response = client.get(reverse("favorites"), headers=HTMX)

    assertContains(response, ">Default</span>", count=1)


@pytest.mark.django_db
def test_favorite_links_carry_their_default_url_and_state(client):
    # The summary card's "🏠 Make default" button reads these from the sidebar.
    user = UserFactory()
    home = FavoriteFactory(user=user, is_default=True)
    other = FavoriteFactory(user=user)
    client.force_login(user)

    response = client.get(reverse("favorites"), headers=HTMX)

    assertContains(response, f'data-set-default-url="{default_url(home)}" data-default')
    assertContains(response, f'data-set-default-url="{default_url(other)}"\n')


@pytest.mark.django_db
def test_summary_card_has_a_default_button_only_for_logged_in_users(
    client, mocked_responses
):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    params = {"lat": "40.7484", "lon": "-73.9967", "name": "New York"}

    anonymous = client.get(reverse("weather"), params, headers=HTMX)
    client.force_login(UserFactory())
    logged_in = client.get(reverse("weather"), params, headers=HTMX)

    assertNotContains(anonymous, "data-default-button")
    assertContains(
        logged_in, 'data-default-button data-lat="40.7484" data-lon="-73.9967"'
    )
