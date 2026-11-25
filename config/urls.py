from django.contrib import admin
from django.urls import include, path

from weather.views import dashboard

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("accounts/", include("accounts.urls")),
    path("weather/", include("weather.urls")),
    path("admin/", admin.site.urls),
]
