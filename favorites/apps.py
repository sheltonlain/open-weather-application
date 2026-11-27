from django.apps import AppConfig


class FavoritesConfig(AppConfig):
    name = "favorites"

    def ready(self) -> None:
        """Connect the after-login hook that saves a pending favorite."""
        from favorites import signals  # noqa: F401
