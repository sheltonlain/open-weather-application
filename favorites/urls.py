from django.urls import path

from favorites import views

urlpatterns = [
    path("", views.favorites, name="favorites"),
    path("<int:pk>/", views.remove_favorite, name="remove_favorite"),
    path("<int:pk>/default/", views.default_favorite, name="default_favorite"),
]
