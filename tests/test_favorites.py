"""Tests for saving, listing, and removing favorites."""

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertRedirects,
    assertTemplateNotUsed,
    assertTemplateUsed,
)

from favorites.models import Favorite
from tests.factories import FavoriteFactory, UserFactory
from tests.openweather import GEO_DIRECT_URL, WEATHER_URL, load_fixture

HTMX = {"HX-Request": "true"}
LONDON = {
    "name": "London",
    "state": "England",
    "country": "GB",
    "lat": "51.5073219",
    "lon": "-0.1276474",
}


@pytest.mark.django_db
def test_saving_a_place_twice_keeps_one_favorite_and_explains_why():
    # A crash must show up as a 500 status, not as a test error.
    client = Client(raise_request_exception=False)
    user = UserFactory()
    FavoriteFactory(user=user, name="London", lat=51.5073, lon=-0.1276)
    client.force_login(user)

    # Same place as the saved one once rounded to 4 decimals.
    response = client.post(
        reverse("favorites"),
        {"name": "London", "country": "GB", "lat": "51.50732", "lon": "-0.12764"},
        headers=HTMX,
    )

    assert response.status_code == 200
    assert "already in your favorites" in response.content.decode()
    assert Favorite.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_deleting_another_users_favorite_returns_404_and_keeps_it(client):
    owner, intruder = UserFactory(), UserFactory()
    favorite = FavoriteFactory(user=owner)
    client.force_login(intruder)

    response = client.delete(
        reverse("remove_favorite", args=[favorite.pk]), headers=HTMX
    )

    assert response.status_code == 404
    assert Favorite.objects.filter(pk=favorite.pk).exists()


@pytest.mark.django_db
def test_anonymous_htmx_save_redirects_the_page_to_login(client):
    response = client.post(
        reverse("favorites"),
        {"name": "London", "lat": "51.5073", "lon": "-0.1276"},
        headers={**HTMX, "HX-Current-URL": "http://testserver/"},
    )

    # HTMX follows HX-Redirect with a full page load, so the login page is
    # shown instead of being swapped into the sidebar.
    assert response.headers.get("HX-Redirect") == "/accounts/login/?next=/"
    assert not Favorite.objects.exists()


# --- Adding -----------------------------------------------------------------


@pytest.mark.django_db
def test_adding_a_favorite_returns_201_and_the_updated_list(client):
    user = UserFactory()
    client.force_login(user)

    response = client.post(reverse("favorites"), LONDON, headers=HTMX)

    assert response.status_code == 201
    assertTemplateUsed(response, "favorites/partials/favorites_list.html")
    assertTemplateNotUsed(response, "base.html")
    assertContains(response, "London, England, GB", status_code=201)
    favorite = Favorite.objects.get(user=user)
    assert (float(favorite.lat), float(favorite.lon)) == (51.5073, -0.1276)


@pytest.mark.django_db
def test_adding_without_htmx_redirects_to_the_dashboard(client):
    client.force_login(UserFactory())

    response = client.post(reverse("favorites"), LONDON, follow=True)

    assertRedirects(response, reverse("dashboard"))
    assertContains(response, "Saved London, England, GB to your favorites.")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "bad",
    [{"lat": "north"}, {"lat": "91"}, {"lon": "-181"}, {"name": ""}],
)
def test_adding_invalid_data_returns_400_and_saves_nothing(client, bad):
    client.force_login(UserFactory())

    response = client.post(reverse("favorites"), {**LONDON, **bad}, headers=HTMX)

    assert response.status_code == 400
    assert not Favorite.objects.exists()


@pytest.mark.django_db
def test_two_users_can_save_the_same_place(client):
    FavoriteFactory(lat=51.5073, lon=-0.1276)
    client.force_login(UserFactory())

    response = client.post(reverse("favorites"), LONDON, headers=HTMX)

    assert response.status_code == 201
    assert Favorite.objects.count() == 2


# --- Listing and switching --------------------------------------------------


@pytest.mark.django_db
def test_list_shows_only_the_current_users_favorites(client):
    user = UserFactory()
    FavoriteFactory(user=user, name="Mine")
    FavoriteFactory(name="Someone Else")
    client.force_login(user)

    for url in (reverse("favorites"), reverse("dashboard")):
        response = client.get(url)
        assertContains(response, "Mine, England, GB")
        assertNotContains(response, "Someone Else")


@pytest.mark.django_db
def test_list_htmx_returns_partial_and_normal_request_full_page(client):
    client.force_login(UserFactory())

    partial = client.get(reverse("favorites"), headers=HTMX)
    page = client.get(reverse("favorites"))

    assertTemplateNotUsed(partial, "base.html")
    assertTemplateUsed(page, "base.html")


@pytest.mark.django_db
def test_clicking_a_favorite_loads_weather_from_its_stored_coordinates(
    client, mocked_responses
):
    user = UserFactory()
    FavoriteFactory(
        user=user,
        name="New York",
        state="New York",
        country="US",
        lat=40.7484,
        lon=-73.9967,
    )
    client.force_login(user)

    sidebar = client.get(reverse("favorites"), headers=HTMX)
    url = (
        f"{reverse('weather')}?lat=40.7484&amp;lon=-73.9967"
        "&amp;name=New+York&amp;state=New+York&amp;country=US"
    )
    assertContains(sidebar, f'hx-get="{url}"')
    assertContains(sidebar, 'hx-target="#weather-panel"')

    # Following that link calls the weather API only: no re-geocoding.
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))
    panel = client.get(url.replace("&amp;", "&"), headers=HTMX)
    assertContains(panel, "New York, New York, US")
    called = [call.request.url for call in mocked_responses.calls]
    assert not any(url.startswith(GEO_DIRECT_URL) for url in called)


# --- Removing ---------------------------------------------------------------


@pytest.mark.django_db
def test_deleting_your_favorite_removes_it_and_returns_the_list(client):
    user = UserFactory()
    keep = FavoriteFactory(user=user, name="Keep")
    gone = FavoriteFactory(user=user, name="Gone")
    client.force_login(user)

    response = client.delete(reverse("remove_favorite", args=[gone.pk]), headers=HTMX)

    assert response.status_code == 200
    assertContains(response, "Keep, England, GB")
    assertNotContains(response, "Gone, England, GB")
    assert list(Favorite.objects.all()) == [keep]


@pytest.mark.django_db
def test_remove_only_accepts_delete(client):
    favorite = FavoriteFactory()
    client.force_login(favorite.user)

    response = client.post(reverse("remove_favorite", args=[favorite.pk]))

    assert response.status_code == 405
    assert Favorite.objects.exists()


# --- Login and CSRF ---------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "post", "delete"])
def test_anonymous_non_htmx_requests_redirect_to_login(client, method):
    favorite = FavoriteFactory()
    url = reverse("favorites")
    if method == "delete":
        url = reverse("remove_favorite", args=[favorite.pk])

    response = getattr(client, method)(url)

    assertRedirects(
        response, f"{reverse('login')}?next={url}", fetch_redirect_response=False
    )
    assert Favorite.objects.count() == 1


@pytest.mark.django_db
def test_anonymous_sees_login_prompt_and_save_buttons(client, mocked_responses):
    mocked_responses.get(GEO_DIRECT_URL, json=load_fixture("geo_direct_paris_tx.json"))

    dashboard = client.get(reverse("dashboard"))
    results = client.get(reverse("search"), {"q": "Paris"}, headers=HTMX)

    assertContains(dashboard, "to save places")
    assertContains(dashboard, 'id="favorites-list"')
    assertContains(results, 'hx-post="/favorites/"')


@pytest.mark.django_db
def test_add_and_delete_without_csrf_token_are_rejected():
    favorite = FavoriteFactory()
    client = Client(enforce_csrf_checks=True)
    client.force_login(favorite.user)

    add = client.post(reverse("favorites"), LONDON, headers=HTMX)
    delete = client.delete(reverse("remove_favorite", args=[favorite.pk]), headers=HTMX)

    assert add.status_code == 403
    assert delete.status_code == 403
    assert list(Favorite.objects.all()) == [favorite]


# --- Save buttons -----------------------------------------------------------


@pytest.mark.django_db
def test_weather_panel_has_a_save_button_for_the_place_shown(client, mocked_responses):
    mocked_responses.get(WEATHER_URL, json=load_fixture("weather_new_york.json"))

    response = client.get(
        reverse("weather"),
        {"lat": "40.7484", "lon": "-73.9967", "name": "New York", "country": "US"},
        headers=HTMX,
    )

    assertContains(response, 'hx-post="/favorites/"')
    assertContains(response, 'hx-target="#favorites-list"')
    assertContains(response, 'name="name" value="New York"')
    assertContains(response, 'name="lat" value="40.7484"')
