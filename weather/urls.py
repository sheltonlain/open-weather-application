from django.urls import path

from weather import views

urlpatterns = [
    path("", views.weather_panel, name="weather"),
    path("search/", views.search, name="search"),
    path("badge/", views.weather_badge, name="weather_badge"),
]
