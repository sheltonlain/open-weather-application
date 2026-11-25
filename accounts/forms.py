from django.contrib.auth.forms import UserCreationForm

from accounts.models import User


class RegisterForm(UserCreationForm):
    """Sign-up form for the custom user: username and password twice."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)
