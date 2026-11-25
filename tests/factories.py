"""factory_boy factories for test data."""

import factory
from django.contrib.auth import get_user_model

DEFAULT_PASSWORD = "a-Strong-pass-42"


class UserFactory(factory.django.DjangoModelFactory):
    """A user whose password is DEFAULT_PASSWORD."""

    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.django.Password(DEFAULT_PASSWORD)
