from django.contrib import admin

from favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["name", "state", "country", "lat", "lon", "user", "created_at"]
    list_filter = ["country"]
