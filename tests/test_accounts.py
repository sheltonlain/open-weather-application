"""Tests for registration, login, logout, and the auth-aware header."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from tests.factories import DEFAULT_PASSWORD, UserFactory

User = get_user_model()


def register(client, username="alice", password1=DEFAULT_PASSWORD, password2=None):
    """POST the registration form; password2 defaults to password1."""
    return client.post(
        reverse("register"),
        {
            "username": username,
            "password1": password1,
            "password2": password2 if password2 is not None else password1,
        },
    )


def logged_in_user_id(client):
    return client.session.get("_auth_user_id")


# Registration


@pytest.mark.django_db
def test_valid_registration_creates_user_logs_in_and_redirects(client):
    response = client.post(
        reverse("register"),
        {
            "username": "alice",
            "password1": "a-Strong-pass-42",
            "password2": "a-Strong-pass-42",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    user = User.objects.get(username="alice")
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
def test_new_user_defaults_to_metric_units(client):
    register(client)

    assert User.objects.get(username="alice").units == User.Units.METRIC


@pytest.mark.django_db
def test_register_page_renders_form(client):
    response = client.get(reverse("register"))

    assert response.status_code == 200
    assertContains(response, 'name="password2"')


@pytest.mark.django_db
def test_registration_with_taken_username_shows_error(client):
    UserFactory(username="alice")

    response = register(client, username="alice")

    assert response.status_code == 200
    assert response.context["form"].has_error("username")
    assertContains(response, "already exists")
    assert User.objects.filter(username="alice").count() == 1
    assert logged_in_user_id(client) is None


@pytest.mark.django_db
def test_registration_with_mismatched_passwords_shows_error(client):
    response = register(client, password2="a-Different-pass-99")

    assert response.status_code == 200
    assert response.context["form"].has_error("password2")
    assertContains(response, "didn’t match")
    assert not User.objects.filter(username="alice").exists()


@pytest.mark.django_db
def test_registration_with_weak_password_shows_error(client):
    response = register(client, password1="password")

    assert response.status_code == 200
    assert response.context["form"].has_error("password2")
    assert not User.objects.filter(username="alice").exists()


# Login


@pytest.mark.django_db
def test_login_with_valid_credentials_logs_in_and_redirects(client):
    user = UserFactory()

    response = client.post(
        reverse("login"), {"username": user.username, "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    assert logged_in_user_id(client) == str(user.pk)


@pytest.mark.django_db
def test_login_with_wrong_password_shows_error(client):
    user = UserFactory()

    response = client.post(
        reverse("login"), {"username": user.username, "password": "wrong-password"}
    )

    assert response.status_code == 200
    assertContains(response, "correct username and password")
    assert logged_in_user_id(client) is None


# Logout


@pytest.mark.django_db
def test_logout_via_get_is_not_allowed(client):
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("logout"))

    assert response.status_code == 405
    assert logged_in_user_id(client) == str(user.pk)


@pytest.mark.django_db
def test_logout_via_post_logs_out_and_redirects(client):
    client.force_login(UserFactory())

    response = client.post(reverse("logout"))

    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    assert logged_in_user_id(client) is None


# Header


@pytest.mark.django_db
def test_header_for_anonymous_shows_login_and_register_links(client):
    response = client.get(reverse("dashboard"))

    assertContains(response, f'href="{reverse("login")}"')
    assertContains(response, f'href="{reverse("register")}"')
    assertNotContains(response, f'action="{reverse("logout")}"')


@pytest.mark.django_db
def test_header_for_logged_in_user_shows_username_and_logout(client):
    client.force_login(UserFactory(username="alice"))

    response = client.get(reverse("dashboard"))

    assertContains(response, "alice")
    assertContains(response, f'action="{reverse("logout")}"')
    assertNotContains(response, f'href="{reverse("login")}"')
