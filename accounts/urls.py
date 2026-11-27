from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("units/", views.set_units, name="set_units"),
    path("settings/", views.settings, name="settings"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
