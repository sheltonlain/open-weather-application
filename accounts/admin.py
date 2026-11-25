from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin for the custom user, showing the units preference."""

    fieldsets = UserAdmin.fieldsets + (("Preferences", {"fields": ("units",)}),)
    list_display = UserAdmin.list_display + ("units",)
